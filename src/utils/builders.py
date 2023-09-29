from typing import List

from utils.environment import Environment
from utils.notifiers.base import Notifier
from utils.notifiers.slack import SlackNotifier
from utils.notifiers.telegram import TelegramNotifier
from utils.storages.aws import AWSStorage
from utils.storages.base import Storage
from utils.storages.local import LocalStorage
from utils.storages.remote import RemoteStorage
from utils.targets.base import Target
from utils.targets.directory import DirectoryTarget
from utils.targets.file import FileTarget
from utils.targets.postgresql import PostgreSQLTarget


class TargetBuilder:

    def __init__(self, builder_config: dict, environment: Environment, namespace: str = None):
        self.builder_config = builder_config
        self.environment = environment
        self.namespace = namespace

    def build_storage_from_config(self, storage_config: dict):
        if storage_config.get('type') == 'aws':
            return AWSStorage(
                **(storage_config.get('params', {})),
                environment=self.environment,
                namespace=self.namespace,
            )
        elif storage_config.get('type') == 'local':
            return LocalStorage(
                **(storage_config.get('params', {})),
                environment=self.environment,
                namespace=self.namespace,
            )
        elif storage_config.get('type') == 'remote':
            return RemoteStorage(
                **(storage_config.get('params', {})),
                environment=self.environment,
                namespace=self.namespace,
            )

    def build_notifier_from_config(self, notifier_config: dict):
        if notifier_config.get('type') == 'slack':
            return SlackNotifier(
                **(notifier_config.get('params', {})),
                environment=self.environment,
                namespace=self.namespace,
            )
        elif notifier_config.get('type') == 'telegram':
            return TelegramNotifier(
                **(notifier_config.get('params', {})),
                environment=self.environment,
                namespace=self.namespace,
            )

    def build_target_from_config(self, target_config: dict, storages: List[Storage], notifiers: List[Notifier]):
        if target_config.get('type') == 'postgresql':
            return PostgreSQLTarget(
                **(target_config.get('params', {})),
                storages=storages,
                notifiers=notifiers,
                environment=self.environment,
                namespace=self.namespace,
            )
        elif target_config.get('type') == 'file':
            return FileTarget(
                **(target_config.get('params', {})),
                storages=storages,
                notifiers=notifiers,
                environment=self.environment,
                namespace=self.namespace,
            )
        elif target_config.get('type') == 'directory':
            return DirectoryTarget(
                **(target_config.get('params', {})),
                storages=storages,
                notifiers=notifiers,
                environment=self.environment,
                namespace=self.namespace,
            )

    def build(self) -> Target:
        storages = []
        for storage_config in self.builder_config.get('storages', []):
            if type(storage_config) is dict:
                storages.append(self.build_storage_from_config(storage_config))

        notifiers = []
        for notifier_config in self.builder_config.get('notifiers', []):
            if type(notifier_config) is dict:
                notifiers.append(self.build_notifier_from_config(notifier_config))

        target = self.build_target_from_config(self.builder_config.get('target', {}), storages, notifiers)

        return target
