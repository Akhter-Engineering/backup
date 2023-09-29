import logging
from abc import ABC, abstractmethod

from utils.environment import Environment

logger = logging.getLogger(__name__)


class Storage(ABC):

    def __init__(self, environment: Environment, namespace: str | None):
        self.environment = environment
        self.namespace = namespace

    @abstractmethod
    def upload(self, source: str, output: str):
        pass
