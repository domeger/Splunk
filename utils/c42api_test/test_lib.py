# Copyright (c) 2015 - 2016 Code42 Software, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""A file for any testing utilities."""

import os
import sys
import functools
from nose.tools import nottest

from c42api import storage_server

class WriteTester(object):
    """
    Class representing an output stream. It may be written to using write(),
    similar to sys.stdout.write() or f.write().

    Internally, a list is maintained, each index corresponding to a line of
    the output "file".
    """
    def __init__(self):
        self.line_list = []

    def write(self, text):
        """
        Append this text to the end of the list of lines.

        :param text: A string to simulate "writing".
        """
        self.line_list.append(text)

    def lines(self):
        """
        :return: The list of string "lines" that were "written".
        """
        return self.line_list


# pylint: disable=too-few-public-methods
class _Nullified(object):
    """A private internal class used to set stderr to devnull temporarily."""
    def __enter__(self):
        """Sets stderr to devnull on enter"""
        sys.stderr = open(os.devnull, 'w')

    def __exit__(self, *_):
        """Sets stderr back to stderr on exit"""
        sys.stderr = sys.__stderr__


# decorator
def warning_to_null(func):
    """Function decorator to pipe all stderr to devnull"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """The wrapper function for the decorator to return"""
        with _Nullified():
            return func(*args, **kwargs)
    return wrapper

class _DisabledStorage(object):
    """A private internal class used to disable storage servers temporarily."""
    def __enter__(self):
        """Cache original implementation of storage_servers and swizzle custom function"""
        storage_server.old_storage_servers = storage_server.storage_servers
        storage_server.storage_servers = self.storage_servers

    def __exit__(self, *_):
        """Return the original implementation of storage_servers"""
        storage_server.storage_servers = storage_server.old_storage_servers

    @staticmethod
    def storage_servers(authority, **_):
        """Function that overwrites storage_servers for skipping authorization"""
        yield authority, None


def disable_storage_server(func):
    """Disable storage server authorization and always use master"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """The wrapper function for the decorator to return"""
        with _DisabledStorage():
            return func(*args, **kwargs)
    return wrapper

@nottest
def run_all_tests():
    """Inspects the currently running test module and runs every test"""
    import inspect
    all_functions = inspect.getmembers(sys.modules['__main__'], inspect.isfunction)
    for name, func in all_functions:
        if name.startswith('test'):
            sys.stdout.write(name + "\n")
            func()

def reload_modules_post_execution(*args):
    """
    Give modules as args, reloads them after function is executed
    """
    def wrap(func):
        """
        Wrapping function
        """
        @functools.wraps(func)
        def wrapped_f():
            """
            Wrapped wrapper
            """
            func()
            for arg in args:
                reload(arg)

        return wrapped_f
    return wrap
