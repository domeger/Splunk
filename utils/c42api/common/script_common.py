"""
A collection of basic helper functions for several scripts.
"""

# pylint: disable=import-error
import sys
import contextlib
import os
import functools


@contextlib.contextmanager
def smart_open(filename, overwrite=False):
    """
    Opens a file if there is a filename, otherwise defaults to stdout and will
    automatically close the file once it's done being used.

    :param filename:  Maybe a filename
    :param overwrite: Whether or not to overwrite said file or to append
    :return:          Yields either an open file or stdout based on input
    """
    if filename and filename != '-':
        style = 'w' if overwrite else 'a'
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        handle = open(filename, style)
    else:
        handle = sys.stdout

    try:
        yield handle
    finally:
        if handle is not sys.stdout:
            handle.close()


# decorator
def memoize(func):
    """
    A decorator that caches output based on input.

    :param func: The function to cache the results of
    :return:     The new function with the cache built in
    """
    memo = {}

    @functools.wraps(func)
    def memoized_func(*args, **kwargs):
        """
        The wrapper function for the memoize decorator
        """
        if args not in memo:
            result = func(*args, **kwargs)
            if result:
                memo[args] = result
        return memo[args]

    return memoized_func
