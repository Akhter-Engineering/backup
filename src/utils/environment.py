import logging
import os

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
