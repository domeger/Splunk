"""
Simple ThreadPool implementation

http://code.activestate.com/recipes/577187-python-thread-pool/
"""

from threading import Thread
from Queue import Queue
from c42api.common import logging_config
# pylint: disable=broad-except

LOG = logging_config.get_logger(__name__)


class Worker(Thread):
    """
    Worker Thread. Pull tasks off the task queue
    and does work.
    """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        """
        Worker thread's run loop
        """
        while True:
            func, args, kwargs = self.tasks.get()
            try:
                func(*args, **kwargs)
            except Exception as exception:
                LOG.exception(exception)

            self.tasks.task_done()


class ThreadPool(object):
    """
    Manages creation of workers and pushing tasks to them
    """
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """
        Adds a task for a worker to grab
        """
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """
        Block until all tasks are done
        """
        self.tasks.join()
