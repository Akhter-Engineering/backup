import logging
from abc import ABC, abstractmethod

from utils.environment import Environment

logger = logging.getLogger(__name__)


class Notifier(ABC):

    def __init__(self, environment: Environment, namespace: str | None):
        self.environment = environment
        self.namespace = namespace

    @abstractmethod
    def notify(self, text):
        pass
