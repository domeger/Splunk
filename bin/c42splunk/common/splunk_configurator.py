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
