import logging
import shutil

from utils.environment import Environment
from utils.functions import retry_if_exception_for_method
from utils.storages.base import Storage

logger = logging.getLogger(__name__)


STORAGE_RETRY_COUNT = 2
STORAGE_RETRY_SLEEP = 5


class LocalStorage(Storage):

    def __init__(
        self,
        backup_path: str,
        environment: Environment,
        namespace: str | None,
    ):
        super(LocalStorage, self).__init__(environment, namespace)
        self.backup_path = backup_path

    @retry_if_exception_for_method(STORAGE_RETRY_COUNT, STORAGE_RETRY_SLEEP)
    def upload(self, source: str, output: str):
        logger.info("LocalStorage -> upload('%s', '%s')" % (source, output))
        shutil.copyfile(source, self.backup_path + '/' + output)

    def describe(self):
        return '(Local directory path: %s)' % (self.backup_path,)
