import logging
from datetime import datetime
from multiprocessing import Process
from typing import Callable, List, Tuple

import croniter
from utils.patterns import Singleton

logger = logging.getLogger(__name__)


class CronService(metaclass=Singleton):

    crons_iters: List[croniter.croniter] = []
    pendings: List[Tuple] = []
    processes: List[Process] = []

    def __init__(self):
        pass

    def add_func(self, cron_expression: str, func: Callable, *args, **kwargs):
        cron_iter = croniter.croniter(cron_expression, datetime.now())
        self.crons_iters.append(cron_iter)
        self.pendings.append((cron_iter.get_next(datetime), func, args, kwargs))

    def clear_finished_processes(self):
        processes: List[Process] = []
        for process in self.processes:
            v = process.exitcode
            if v is None:
                processes.append(process)
        self.processes = processes

    def run_pending(self):
        current_dt = datetime.now()
        for index, (at, func, args, kwargs) in enumerate(self.pendings):
            if at < current_dt:
                process = Process(target=func, args=args, kwargs=kwargs)
                process.start()
                logger.info("Start function %s with args %s and kwargs %s (PID: %s)" % (func, args, kwargs, process.pid))
                self.processes.append(process)
                try:
                    self.pendings[index] = (self.crons_iters[index].get_next(datetime), func, args, kwargs)
                except croniter.CroniterBadDateError:
                    self.pendings.pop(index)
                    self.crons_iters.pop(index)
        self.clear_finished_processes()
