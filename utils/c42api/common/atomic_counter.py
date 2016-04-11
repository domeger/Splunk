"""
Count things....atomically
"""

from threading import Lock


class AtomicCounter(object):
    """
    Atomically Count things
    """
    def __init__(self, count):
        self._lock = Lock()
        self._count = count

    def set(self, value):
        """Read the function name"""
        with self._lock:
            self._count = value

    def decrement(self):
        """Read the function name"""
        with self._lock:
            self._count = self._count - 1

    def increment(self):
        """Read the function name"""
        with self._lock:
            self._count = self._count + 1

    def get(self):
        """Read the function name"""
        with self._lock:
            return self._count
