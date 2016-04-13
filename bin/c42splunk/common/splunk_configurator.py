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

"""
A file for a class that holds common state for a splunk script.
"""

import os


class SplunkConfigurator(object):
    """
    A class that holds common state for a splunk script. Specifically, it
    stores the session key and provides access to the splunk home location.
    """
    def __init__(self):
        """Initializes instance variables for properties"""
        self._session_key = None
        self._splunk_home = None
        self._is_initialized = False

    def initialize(self, session_key):
        """Sets the session key instance variable, but only once"""
        if self._is_initialized:
            return
        self._session_key = session_key
        self._is_initialized = True

    @property
    def session_key(self):
        """The getter for the immutable session_key"""
        return self._session_key

    @property
    def splunk_home(self):
        """The getter for the lazily instantiated splunk_home"""
        if not self._splunk_home:
            self._splunk_home = os.environ.get('SPLUNK_HOME')
        return self._splunk_home
