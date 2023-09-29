#!python


import logging
import time
from multiprocessing import Process
from typing import List

import schedule
import urllib3
from services.cron import CronService
from utils.builders import TargetBuilder
from utils.config import Config
from utils.environment import Environment
from utils.targets.base import Target

urllib3.disable_warnings()

# Logging

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[PID: %(process)d] - %(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logging.basicConfig(level=logging.INFO, handlers=[handler])

logger = logging.getLogger(__name__)


def backup(environment: Environment):
    logger.info(">> Starting backup")

    targets: List[Target] = []

    if environment.USE_CONFIG == 'on':  # type: ignore
        config = Config.load_config_from_string(environment.CONFIG)  # type: ignore
        for namespace, builder_config in config.items():
            target_builder = TargetBuilder(builder_config, environment, namespace)
            targets.append(target_builder.build())
    else:
        config = Config.load_config_from_old_style()
        target_builder = TargetBuilder(config, environment)
        targets.append(target_builder.build())

    processes: List[Process] = []
    for target in targets:
        process = Process(target=target.backup)
        process.start()
        if target.namespace is not None:
            logger.info("Start target backup (PID: %s): %s (%s)" % (process.pid, type(target), target.namespace))
        else:
            logger.info("Start target backup (PID: %s): %s" % (process.pid, type(target),))
        processes.append(process)

    for process in processes:
        process.join()

    logger.info(">> Finished backup")


if __name__ == '__main__':
    environment: Environment = Environment()
    cron_service = CronService()

    cron_service.add_func(environment.CRON_EXPRESSION, backup, environment)  # type: ignore

    schedule.every(1).seconds.do(cron_service.run_pending)

    while True:
        schedule.run_pending()
        time.sleep(1)
