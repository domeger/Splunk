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
Collection of files with state and functions that are common to multiple
scripts. This file also adds any local packages to the path.
"""

# pylint: disable=relative-import
from splunk_configurator import SplunkConfigurator
import sys
import os
import errno


CONFIG = SplunkConfigurator()
APP_HOME = os.path.join(CONFIG.splunk_home, 'etc', 'apps', 'code42')
EVENTS_DIR = os.path.join(APP_HOME, 'events')
ANALYTICS_DIR = os.path.join(EVENTS_DIR, 'analytics')
try:
    os.makedirs(ANALYTICS_DIR)
except OSError as exc:
    if exc.errno != errno.EEXIST or not os.path.isdir(ANALYTICS_DIR):
        raise

sys.path.insert(0, os.path.join(APP_HOME, 'bin'))
sys.path.insert(0, os.path.join(APP_HOME, 'utils'))

WHEEL_DIR = os.path.join(APP_HOME, 'utils', 'wheels')
EGG_DIR = os.path.join(APP_HOME, 'utils', 'eggs')


def add_wheel(wheel_name):
    """
    Adds a wheel to the python path
    """
    sys.path.insert(0, os.path.join(WHEEL_DIR, wheel_name))


def add_egg(egg_name):
    """
    Adds an egg to the python path
    """
    sys.path.insert(0, os.path.join(EGG_DIR, egg_name))

WHEELS = [
    'six-1.9.0-py2.py3-none-any.whl',
    'python_dateutil-2.4.2-py2.py3-none-any.whl',
    'requests-2.7.0-py2.py3-none-any.whl',
]
EGGS = [
]

# pylint: disable=bad-builtin
map(add_wheel, WHEELS)
map(add_egg, EGGS)
