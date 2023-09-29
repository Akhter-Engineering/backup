import logging
from typing import List

import requests
from utils.environment import Environment
from utils.functions import retry_if_exception_for_method
from utils.notifiers.base import Notifier

logger = logging.getLogger(__name__)


NOTIFIER_RETRY_COUNT = 3
NOTIFIER_RETRY_SLEEP = 3


class TelegramNotifier(Notifier):

    def __init__(
        self,
        chat_ids: List[str],
        bot_token: str,
        environment: Environment,
        namespace: str | None,
    ):
        super(TelegramNotifier, self).__init__(environment, namespace)
        self.chat_ids = chat_ids
        self.bot_token = bot_token

    @retry_if_exception_for_method(NOTIFIER_RETRY_COUNT, NOTIFIER_RETRY_SLEEP)
    def notify(self, text: str):
        logger.info("TelegramNotifier -> notify('%s')" % text)
        for chat_id in self.chat_ids:
            if type(chat_id) in (tuple, list):
                url = "https://api.telegram.org/bot%(bot_token)s/sendMessage?chat_id=%(chat_id)s&text=%(text)s&reply_to_message_id=%(reply_to_message_id)s" % {
                    'bot_token': self.bot_token,
                    'chat_id': chat_id[0],
                    'text': text,
                    'reply_to_message_id': chat_id[1],
                }
            else:
                url = "https://api.telegram.org/bot%(bot_token)s/sendMessage?chat_id=%(chat_id)s&text=%(text)s" % {
                    'bot_token': self.bot_token,
                    'chat_id': chat_id,
                    'text': text,
                }
            resp = requests.get(url, verify=False).json()  # nosec B501
            if not resp['ok']:
                assert resp
