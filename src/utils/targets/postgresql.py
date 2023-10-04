import logging
import os
import shlex
from datetime import datetime
from typing import List

from utils.environment import Environment
from utils.functions import retry_if_exception_for_method
from utils.notifiers.base import Notifier
from utils.storages.base import Storage
from utils.targets.base import Target
from utils.io import delete_file_if_exists

logger = logging.getLogger(__name__)


TARGET_RETRY_COUNT = 2
TARGET_RETRY_SLEEP = 5


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
        namespace: str | None,
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
        exit_code = os.system('PGPASSWORD=%(postgres_password)s pg_dump --no-owner --no-privileges -h %(postgres_host)s -p %(postgres_port)s -U %(postgres_user)s %(postgres_db)s -f %(path)s -F plain' % {  # nosec B605
            'path': shlex.quote(path),
            'postgres_host': shlex.quote(self.postgres_host),
            'postgres_port': shlex.quote(self.postgres_port),
            'postgres_db': shlex.quote(self.postgres_db),
            'postgres_user': shlex.quote(self.postgres_user),
            'postgres_password': shlex.quote(self.postgres_password),
        })
        if exit_code != 0:
            raise Exception("pg_dump failed with the exit code: %s" % exit_code)

    @retry_if_exception_for_method(TARGET_RETRY_COUNT, TARGET_RETRY_SLEEP)
    def backup(self):
        logger.info("PostgreSQLTarget -> backup")
        app_name = self.environment.APP_NAME

        output_filename = self.get_output_filename()
        temp_path = '/tmp/%s' % output_filename

        try:
            self.create_temp_backup_sql(temp_path)

            for storage in self.storages:
                storage.upload(temp_path, output_filename)

                for notifier in self.notifiers:
                    notifier.notify(
                        "💚 Created a postgresql backup `%s` for application `%s` in storage `%s`" % (output_filename, app_name, storage.describe()),
                    )

        except Exception as e:
            for notifier in self.notifiers:
                notifier.notify(
                    "💔 Error: `%s` ```%s```" % (app_name, e),
                )
            raise e
        finally:
            delete_file_if_exists(temp_path)
