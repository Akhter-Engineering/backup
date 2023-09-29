import logging
import time
from typing import Callable

logger = logging.getLogger(__name__)


def retry_if_exception(times: int, sleep: int):
    def _retry(func: Callable):
        def _func(*args, **kwargs):
            _times = times

            while _times > 0:
                try:
                    _times -= 1
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    exc = e
                    logger.warn(e)

                    logger.info("Sleep %s seconds" % sleep)
                    time.sleep(sleep)

                    logger.info("Retry (left attemps: %s) ..." % _times)
            raise exc
        return _func

    return _retry


def retry_if_exception_for_method(times: int, sleep: int):
    def _retry(func: Callable):
        def _func(self, *args, **kwargs):
            _times = times

            while _times > 0:
                try:
                    _times -= 1
                    result = func(self, *args, **kwargs)
                    return result
                except Exception as e:
                    exc = e
                    logger.warn(e)

                    logger.info("Sleep %s seconds" % sleep)
                    time.sleep(sleep)

                    logger.info("Retry (left attemps: %s) ..." % _times)

            raise exc
        return _func
    return _retry
