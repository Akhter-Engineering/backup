#!python

from asyncio.log import logger
import os
import logging
import boto

from datetime import datetime

from boto.s3.key import Key

from slack import WebClient
from slack.errors import SlackApiError


logging.basicConfig(level=logging.INFO)


class Context:
    
    APP_NAME = 'app_name'
    AWS_REGION = 'aws_region'
    AWS_ACCESS_KEY_ID = 'aws_access_key_id'
    AWS_SECRET_ACCESS_KEY = 'aws_secret_access_key'
    AWS_BUCKET_NAME = 'aws_bucket_name'
    SLACK_CHANNEL = 'slack_channel'
    SLACK_API_TOKEN = 'slack_api_token'

    @staticmethod
    def get_initial_context():
        context = {
            Context.APP_NAME: os.getenv('BACKUP_APP_NAME'),
            Context.AWS_REGION: os.getenv('BACKUP_AWS_REGION'),
            Context.AWS_ACCESS_KEY_ID: os.getenv('BACKUP_AWS_ACCESS_KEY_ID'),
            Context.AWS_SECRET_ACCESS_KEY: os.getenv('BACKUP_AWS_SECRET_ACCESS_KEY'),
            Context.AWS_BUCKET_NAME: os.getenv('BACKUP_AWS_BUCKET_NAME'),
            Context.SLACK_CHANNEL: os.getenv('BACKUP_SLACK_CHANNEL'),
            Context.SLACK_API_TOKEN: os.getenv('BACKUP_SLACK_API_TOKEN'),
        }
        return context


def get_output_filename(prefix_name, context):
    return '%s_%s.sql' % (prefix_name, datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ'))


def create_temp_backup_sql(path, context):
    os.system('PGPASSWORD=$BACKUP_POSTGRES_PASSWORD pg_dump -h $BACKUP_POSTGRES_HOST -p $BACKUP_POSTGRES_PORT -U $BACKUP_POSTGRES_USER $BACKUP_POSTGRES_DB > %s' % path)


def upload_temp_backup_sql_into_s3(source, output, context):
    conn = boto.s3.connect_to_region(
        context.get(Context.AWS_REGION),
        aws_access_key_id=context.get(Context.AWS_ACCESS_KEY_ID),
        aws_secret_access_key=context.get(Context.AWS_SECRET_ACCESS_KEY),
    )
    bucket = conn.get_bucket(context.get(Context.AWS_BUCKET_NAME))
    k = Key(bucket)
    k.key = output
    k.set_contents_from_filename(source)


def notify_backup_result_to_slack(text, context):
    slack_client = WebClient(token=context.get(Context.SLACK_API_TOKEN))
    try:
        response = slack_client.chat_postMessage(
            channel=context.get(Context.SLACK_CHANNEL),
            text=text
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'


def main():
    context = Context.get_initial_context()
    
    try:
        output_filename = get_output_filename(context.get(Context.APP_NAME), context)
        temp_path = '/tmp/%s' % output_filename
        create_temp_backup_sql(temp_path, context)
        upload_temp_backup_sql_into_s3(
            temp_path,
            output_filename,
            context,
        )
        notify_backup_result_to_slack(
            ":green_heart: Created a postgresql backup `%s` for application `%s` in AWS bucket `%s`" % (output_filename, context.get(Context.APP_NAME), context.get(Context.AWS_BUCKET_NAME)),
            context,
        )
    except Exception as e:
        notify_backup_result_to_slack(
            ":broken_heart: Error: `%s` ```%s```" % (context.get(Context.APP_NAME), e),
            context,
        )
        raise e


if __name__ == '__main__':
    main()
