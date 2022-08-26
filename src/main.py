#!python


import os
import logging
import yaml
import shlex
import boto

from typing import List
from abc import ABC, abstractmethod

from datetime import datetime

from boto.s3.key import Key

from slack import WebClient
from slack.errors import SlackApiError


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


ENVIRONMENT_PREFIX = 'BACKUP_'

ENVS = {
    'APP_NAME': None,
    'CRON_EXPRESSION': None,
    'USE_CONFIG': None,
    'CONFIG': None,
}


class Environment:

    def __init__(self):
        for env_name in ENVS:
            self.__setattr__(env_name, ENVS.get(env_name))

        for env_name in ENVS:
            prefixed_env_name = '%s%s' % (ENVIRONMENT_PREFIX, env_name)
            if prefixed_env_name in os.environ:
                self.__setattr__(env_name, os.getenv(prefixed_env_name))


class Config:

    @staticmethod
    def load_config_from_string(plain_text):
        return yaml.safe_load(plain_text)

    @staticmethod
    def load_config_from_old_style():
        return {
            'target': {
                'type': 'postgresql',
                'params': {
                    'postgres_host': os.getenv('BACKUP_POSTGRES_HOST'),
                    'postgres_port': os.getenv('BACKUP_POSTGRES_PORT'),
                    'postgres_db': os.getenv('BACKUP_POSTGRES_DB'),
                    'postgres_user': os.getenv('BACKUP_POSTGRES_USER'),
                    'postgres_password': os.getenv('BACKUP_POSTGRES_PASSWORD'),
                }
            },

            'storages': [
                {
                    'type': "aws",
                    'params': {
                        'aws_bucket_name': os.getenv('BACKUP_AWS_BUCKET_NAME'),
                        'aws_region': os.getenv('BACKUP_AWS_REGION'),
                        'aws_access_key_id': os.getenv('BACKUP_AWS_ACCESS_KEY_ID'),
                        'aws_secret_access_key': os.getenv('BACKUP_AWS_SECRET_ACCESS_KEY'),
                    }
                }
            ],

            'notifiers': [
                {
                    'type': "slack",
                    'params': {
                        'slack_api_token': os.getenv('BACKUP_SLACK_API_TOKEN'),
                        'slack_channels': [
                            os.getenv('BACKUP_SLACK_CHANNEL'),
                        ]
                    }
                }
            ]
        }


class Storage(ABC):

    def __init__(self, environment: Environment, namespace: str):
        self.environment = environment
        self.namespace = namespace

    @abstractmethod
    def upload(self, source: str, output: str):
        pass


class AWSStorage(Storage):

    def __init__(
        self,
        aws_bucket_name: str,
        aws_region: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        environment: Environment,
        namespace: str,
    ):
        super(AWSStorage, self).__init__(environment, namespace)
        self.aws_bucket_name = aws_bucket_name
        self.aws_region = aws_region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

    def upload(self, source: str, output: str):
        logger.info("AWSStorage -> upload('%s', '%s')" % (source, output))
        conn = boto.s3.connect_to_region(
            self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        bucket = conn.get_bucket(self.aws_bucket_name)
        k = Key(bucket)
        k.key = output
        k.set_contents_from_filename(source)

    def describe(self):
        return '(AWS region: %s, S3 Bucket: %s)' % (self.aws_region, self.aws_bucket_name)


class Notifier:
    
    def __init__(self, environment: Environment, namespace: str):
        self.environment = environment
        self.namespace = namespace

    @abstractmethod
    def notify(self, text):
        pass


class SlackNotifier(Notifier):

    def __init__(
        self,
        slack_channels: List[str],
        slack_api_token: str,
        environment: Environment,
        namespace: str,
    ):
        super(SlackNotifier, self).__init__(environment, namespace)
        self.slack_channels = slack_channels
        self.slack_api_token = slack_api_token

    def notify(self, text: str):
        logger.info("SlackNotifier -> notify('%s')" % text)
        for channel in self.slack_channels:
            slack_client = WebClient(token=self.slack_api_token)
            try:
                slack_client.chat_postMessage(channel=channel, text=text)
            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'


class Target:
    
    def __init__(self, storages: List[Storage], notifiers: List[Notifier], environment: Environment, namespace: str):
        self.storages = storages
        self.notifiers = notifiers
        self.environment = environment
        self.namespace = namespace

    @abstractmethod
    def backup(self, text):
        pass


class PostgreSQLTarget(Target):

    def __init__(
        self,
        postgres_host: str,
        postgres_port: str,
        postgres_db: str,
        postgres_user: str,
        postgres_password: str,
        storages: List[Storage],
        notifiers: List[Notifier],
        environment: Environment,
        namespace: str,
    ):
        super(PostgreSQLTarget, self).__init__(storages, notifiers, environment, namespace)
        self.postgres_host = postgres_host
        self.postgres_port = postgres_port
        self.postgres_db = postgres_db
        self.postgres_user = postgres_user
        self.postgres_password = postgres_password
    
    def get_output_filename(self):
        if self.namespace is not None:
            prefix_name = '%s_%s' % (self.environment.APP_NAME, self.namespace)
        else:
            prefix_name = self.environment.APP_NAME
        return '%s_%s.sql' % (prefix_name, datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ'))

    def create_temp_backup_sql(self, path: str):
        logger.info("PostgreSQLTarget -> create_temp_backup_sql('%s')" % path)
        os.system('PGPASSWORD=%(postgres_password)s pg_dump -h %(postgres_host)s -p %(postgres_port)s -U %(postgres_user)s %(postgres_db)s > %(path)s' % {
            'path': shlex.quote(path),
            'postgres_host': shlex.quote(self.postgres_host),
            'postgres_port': shlex.quote(self.postgres_port),
            'postgres_db': shlex.quote(self.postgres_db),
            'postgres_user': shlex.quote(self.postgres_user),
            'postgres_password': shlex.quote(self.postgres_password),
        })

    def backup(self):
        logger.info("PostgreSQLTarget -> backup")
        app_name = self.environment.APP_NAME

        try:
            output_filename = self.get_output_filename()
            temp_path = '/tmp/%s' % output_filename

            self.create_temp_backup_sql(temp_path)

            for storage in self.storages:
                storage.upload(temp_path, output_filename)

                for notifier in self.notifiers:
                    notifier.notify(
                        ":green_heart: Created a postgresql backup `%s` for application `%s` in storage `%s`" % (output_filename, app_name, storage.describe()),
                    )

        except Exception as e:
            for notifier in self.notifiers:
                notifier.notify(
                    ":broken_heart: Error: `%s` ```%s```" % (app_name, e),
                )
            raise e


class TargetBuilder:

    def __init__(self, builder_config: dict, environment: Environment, namespace: str = None):
        self.builder_config = builder_config
        self.environment = environment
        self.namespace = namespace

    def build_storage_from_config(self, storage_config: dict):
        if storage_config.get('type') == 'aws':
            return AWSStorage(
                **(storage_config.get('params')),
                environment=self.environment,
                namespace=self.namespace,
            )

    def build_notifier_from_config(self, notifier_config: dict):
        if notifier_config.get('type') == 'slack':
            return SlackNotifier(
                **(notifier_config.get('params')),
                environment=self.environment,
                namespace=self.namespace,
            )

    def build_target_from_config(self, target_config: dict, storages: List[Storage], notifiers: List[Notifier]):
        if target_config.get('type') == 'postgresql':
            return PostgreSQLTarget(
                **(target_config.get('params')),
                storages=storages,
                notifiers=notifiers,
                environment=self.environment,
                namespace=self.namespace,
            )

    def build(self):
        storages = []
        for storage_config in self.builder_config.get('storages'):
            storages.append(self.build_storage_from_config(storage_config))

        notifiers = []
        for notifier_config in self.builder_config.get('notifiers'):
            notifiers.append(self.build_notifier_from_config(notifier_config))

        target = self.build_target_from_config(self.builder_config.get('target'), storages, notifiers)

        return target


def main():
    environment: Environment = Environment()

    targets: List[Target] = []
    
    if environment.USE_CONFIG == 'on':
        config = Config.load_config_from_string(environment.CONFIG)
        for namespace, builder_config in config.items():
            target_builder = TargetBuilder(builder_config, environment, namespace)
            targets.append(target_builder.build())
    else:
        config = Config.load_config_from_old_style()
        target_builder = TargetBuilder(config, environment)
        targets.append(target_builder.build())

    for target in targets:
        target.backup()


if __name__ == '__main__':
    main()
