import logging
import os
import shutil
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


class DirectoryTarget(Target):

    def __init__(
        self,
        dirpath: str,
        storages: List[Storage],
        notifiers: List[Notifier],
        environment: Environment,
        namespace: str | None,
    ):
        super(DirectoryTarget, self).__init__(storages, notifiers, environment, namespace)
        self.dirpath = dirpath

    def get_output_filename(self):
        if self.namespace is not None:
            prefix_name = '%s_%s' % (self.environment.APP_NAME, self.namespace)
        else:
            prefix_name = self.environment.APP_NAME
        return '%s_%s.zip' % (prefix_name, datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ'))

    def create_archive(self, filepath: str):
        logger.info("DirectoryTarget -> create_archive('%s')" % filepath)
        filename, _ = os.path.splitext(filepath)
        parent_dir = os.path.dirname(self.dirpath)
        relative_dir = os.path.basename(self.dirpath)
        return shutil.make_archive(filename, 'zip', root_dir=parent_dir, base_dir=relative_dir)

    @retry_if_exception_for_method(TARGET_RETRY_COUNT, TARGET_RETRY_SLEEP)
    def backup(self):
        logger.info("DirectoryTarget -> backup")
        app_name = self.environment.APP_NAME

        output_filename = self.get_output_filename()
        temp_path = '/tmp/%s' % output_filename

        try:
            self.create_archive(temp_path)

            for storage in self.storages:
                storage.upload(temp_path, output_filename)

                for notifier in self.notifiers:
                    notifier.notify(
                        "💚 Created a directory backup `%s` for application `%s` in storage `%s`" % (output_filename, app_name, storage.describe()),
                    )

        except Exception as e:
            for notifier in self.notifiers:
                notifier.notify(
                    "💔 Error: `%s` ```%s```" % (app_name, e),
                )
            raise e
        finally:
            delete_file_if_exists(temp_path)
