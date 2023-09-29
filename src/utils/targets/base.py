import logging
from abc import ABC, abstractmethod
from typing import List

from utils.environment import Environment
from utils.notifiers.base import Notifier
from utils.storages.base import Storage

logger = logging.getLogger(__name__)


TARGET_RETRY_COUNT = 2
TARGET_RETRY_SLEEP = 5


class Target(ABC):

    def __init__(self, storages: List[Storage], notifiers: List[Notifier], environment: Environment, namespace: str | None):
        self.storages = storages
        self.notifiers = notifiers
        self.environment = environment
        self.namespace = namespace

    @abstractmethod
    def backup(self, text):
        pass
