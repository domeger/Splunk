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
A wrapper script the computers module in c42api that prints out data to
Splunk lookup tables. This is intended to be called by Splunk.
"""

# pylint: disable=relative-import, import-error
import os

from common import splunk_common as common
import c42api
from splunk_utils import splunk_lookup_table

TIME_KEY = 'modificationDate'
COMPUTER_KEYS_TO_IGNORE = ['lastConnected',
                           'modificationDate',
                           'loginDate']
COMPUTER_UID_KEY = 'guid'


def _run():
    """
    The script's body. Creates/Updates Splunk computer lookup table.
    """
    app_home = common.app_home()

    lookups_dir = os.path.join(app_home, "lookups")
    old_computer_lookup_table = os.path.join(lookups_dir, "computer_lookup.csv")
    tmp_computer_lookup_table = os.path.join(lookups_dir, "computer_lookup_tmp.csv")

    if not os.path.exists(lookups_dir):
        os.makedirs(lookups_dir)

    server, _ = common.setup()

    # write computer lookup table
    params = {'active': 'true',
              'incBackupUsage': False,
              'incHistory': False}
    computer_results = c42api.fetch_computers(server, params, insert_schema_version=True)
    splunk_lookup_table.write_lookup_table(old_computer_lookup_table, tmp_computer_lookup_table, computer_results,
                                           COMPUTER_UID_KEY, COMPUTER_KEYS_TO_IGNORE, TIME_KEY)

if __name__ == '__main__':
    _run()
