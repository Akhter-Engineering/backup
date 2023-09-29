#!python


import logging
import os
from typing import List

from utils.environment import Environment
from utils.functions import retry_if_exception_for_method
from utils.notifiers.base import Notifier
from utils.storages.base import Storage
from utils.targets.base import Target

logger = logging.getLogger(__name__)


TARGET_RETRY_COUNT = 2
TARGET_RETRY_SLEEP = 5


class FileTarget(Target):

    def __init__(
        self,
        filepath: str,
        storages: List[Storage],
        notifiers: List[Notifier],
        environment: Environment,
        namespace: str | None,
    ):
        super(FileTarget, self).__init__(storages, notifiers, environment, namespace)
        self.filepath = filepath

    def get_output_filename(self):
        filename = os.path.basename(self.filepath)
        if self.namespace is not None:
            prefix_name = '%s_%s' % (self.environment.APP_NAME, self.namespace)
        else:
            prefix_name = self.environment.APP_NAME
        return '%s_%s' % (prefix_name, filename)

    @retry_if_exception_for_method(TARGET_RETRY_COUNT, TARGET_RETRY_SLEEP)
    def backup(self):
        logger.info("FileTarget -> backup")
        app_name = self.environment.APP_NAME

        try:
            output_filename = self.get_output_filename()

            for storage in self.storages:
                storage.upload(self.filepath, output_filename)

                for notifier in self.notifiers:
                    notifier.notify(
                        "💚 Created a file backup `%s` for application `%s` in storage `%s`" % (output_filename, app_name, storage.describe()),
                    )

        except Exception as e:
            for notifier in self.notifiers:
                notifier.notify(
                    "💔 Error: `%s` ```%s```" % (app_name, e),
                )
            raise e
