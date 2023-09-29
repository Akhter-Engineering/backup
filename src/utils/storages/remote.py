import logging

import paramiko
from utils.environment import Environment
from utils.functions import retry_if_exception_for_method
from utils.storages.base import Storage

logger = logging.getLogger(__name__)


STORAGE_RETRY_COUNT = 2
STORAGE_RETRY_SLEEP = 5


class RemoteStorage(Storage):

    def __init__(
        self,
        ssh_username: str,
        ssh_password: str,
        ssh_host: str,
        ssh_port: int,
        remote_dir_path: str,
        environment: Environment,
        namespace: str | None,
    ):
        super(RemoteStorage, self).__init__(environment, namespace)
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.remote_dir_path = remote_dir_path

    @retry_if_exception_for_method(STORAGE_RETRY_COUNT, STORAGE_RETRY_SLEEP)
    def upload(self, source: str, output: str):
        logger.info("RemoteStorage -> upload('%s', '%s')" % (source, output))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.ssh_host, port=self.ssh_port, username=self.ssh_username, password=self.ssh_password)
        sftp = ssh.open_sftp()
        sftp.put(source, self.remote_dir_path + '/' + output)
        sftp.close()
        ssh.close()

    def describe(self):
        return '(Remote host: %s, directory path: %s)' % (self.ssh_host, self.remote_dir_path,)
