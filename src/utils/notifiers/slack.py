import logging
from typing import List

from slack import WebClient
from slack.errors import SlackApiError
from utils.environment import Environment
from utils.functions import retry_if_exception_for_method
from utils.notifiers.base import Notifier

logger = logging.getLogger(__name__)


NOTIFIER_RETRY_COUNT = 3
NOTIFIER_RETRY_SLEEP = 3


class SlackNotifier(Notifier):

    def __init__(
        self,
        slack_channels: List[str],
        slack_api_token: str,
        environment: Environment,
        namespace: str | None,
    ):
        super(SlackNotifier, self).__init__(environment, namespace)
        self.slack_channels = slack_channels
        self.slack_api_token = slack_api_token

    @retry_if_exception_for_method(NOTIFIER_RETRY_COUNT, NOTIFIER_RETRY_SLEEP)
    def notify(self, text: str):
        logger.info("SlackNotifier -> notify('%s')" % text)
        for channel in self.slack_channels:
            slack_client = WebClient(token=self.slack_api_token)
            try:
                slack_client.chat_postMessage(channel=channel, text=text)
            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
