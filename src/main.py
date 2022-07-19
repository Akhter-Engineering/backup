#!python

import os
import logging
import boto

from datetime import datetime

from boto.s3.key import Key

from slack import WebClient
from slack.errors import SlackApiError


BACKUP_APP_NAME = os.getenv('BACKUP_APP_NAME')
BACKUP_AWS_ACCESS_KEY_ID = os.getenv('BACKUP_AWS_ACCESS_KEY_ID')
BACKUP_AWS_SECRET_ACCESS_KEY = os.getenv('BACKUP_AWS_SECRET_ACCESS_KEY')
BACKUP_AWS_BUCKET_NAME = os.getenv('BACKUP_AWS_BUCKET_NAME')

BACKUP_SLACK_API_TOKEN = os.getenv('BACKUP_SLACK_API_TOKEN')
BACKUP_SLACK_CHANNEL = os.getenv('BACKUP_SLACK_CHANNEL')


logging.basicConfig(level=logging.INFO)


def get_output_filename():
    return '%s_%s.sql' % (BACKUP_APP_NAME, datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ'))


def create_temp_backup_sql(temp_path):
    os.system('PGPASSWORD=$BACKUP_POSTGRES_PASSWORD pg_dump -h $BACKUP_POSTGRES_HOST -U $BACKUP_POSTGRES_USER $BACKUP_POSTGRES_DB > %s' % temp_path)


def upload_temp_backup_sql_into_s3(source, output):
    conn = boto.s3.connect_to_region(
        'eu-west-1',
        aws_access_key_id = BACKUP_AWS_ACCESS_KEY_ID,
        aws_secret_access_key = BACKUP_AWS_SECRET_ACCESS_KEY
    )
    bucket = conn.get_bucket(BACKUP_AWS_BUCKET_NAME)
    k = Key(bucket)
    k.key = output
    k.set_contents_from_filename(source)


def notify_backup_result_to_slack(channel, text):
    slack_client = WebClient(token=BACKUP_SLACK_API_TOKEN)
    try:
        response = slack_client.chat_postMessage(
            channel=channel,
            text=text
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'


def main():
    try:
        temp_path = 'backup.sql'
        output_filename= get_output_filename()
        create_temp_backup_sql(temp_path)
        upload_temp_backup_sql_into_s3(temp_path, output_filename)
        notify_backup_result_to_slack(BACKUP_SLACK_CHANNEL,
            ":green_heart: Created a postgresql backup `%s` for application `%s` in AWS bucket `%s`" % (output_filename, BACKUP_APP_NAME, BACKUP_AWS_BUCKET_NAME))
    except Exception as e:
        notify_backup_result_to_slack(BACKUP_SLACK_CHANNEL, ":broken_heart: Error: `%s` ```%s```" % (BACKUP_APP_NAME, e))
        raise e


if __name__ == '__main__':
    main()
