import logging
import os

import yaml

logger = logging.getLogger(__name__)


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
                    'type': "local",
                    'params': {
                        'backup_path': os.getenv('BACKUP_PATH'),
                    }
                }
            ],

            'notifiers': [
                {
                    'type': "telegram",
                    'params': {
                        'slack_api_token': os.getenv('bot_token'),
                        'chat_ids': [
                            os.getenv('chat_ids'),
                        ]
                    }
                }
            ]
        }
