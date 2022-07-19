#!python

import os
import logging
import boto

from datetime import datetime

from boto.s3.key import Key

from slack import WebClient
from slack.errors import SlackApiError


APP_NAME = os.getenv('APP_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN')
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')


logging.basicConfig(level=logging.INFO)


def get_output_filename():
    return '%s_%s.sql' % (APP_NAME, datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ'))


def create_temp_backup_sql(temp_path):
    os.system('PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB > %s' % temp_path)


def upload_temp_backup_sql_into_s3(source, output):
    conn = boto.s3.connect_to_region(
        'eu-west-1',
        aws_access_key_id = AWS_ACCESS_KEY_ID,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    )
    bucket = conn.get_bucket(AWS_BUCKET_NAME)
    k = Key(bucket)
    k.key = output
    k.set_contents_from_filename(source)


def notify_backup_result_to_slack(channel, text):
    slack_client = WebClient(token=SLACK_API_TOKEN)
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
        notify_backup_result_to_slack(SLACK_CHANNEL,
            ":green_heart: Created a postgresql backup `%s` for application `%s` in AWS bucket `%s`" % (output_filename, APP_NAME, AWS_BUCKET_NAME))
    except Exception as e:
        notify_backup_result_to_slack(SLACK_CHANNEL, ":broken_heart: Error: `%s` ```%s```" % (APP_NAME, e))
        raise e


if __name__ == '__main__':
    main()
