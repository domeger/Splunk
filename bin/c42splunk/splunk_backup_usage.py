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
A wrapper script around c42api.computers that prints out backup usage data
to stdout. This is intended to be called by Splunk.
"""

# pylint: disable=relative-import, import-error
import datetime
import sys

from common import splunk_common as common
import c42api


def _run():
    """
    The script's body. Prints out backup usage data to stdout, which will be
    captured by Splunk.
    """
    server, _ = common.setup()
    params = {'active': 'true',
              'incBackupUsage': True,
              'incHistory': True}
    results = c42api.fetch_computers(server, params, insert_schema_version=True)
    timestamp = datetime.datetime.now().isoformat()
    for result in results:
        guid = result['guid']
        schema_version = result['schema_version']
        backup_usage_array = result['backupUsage']
        for backup_usage in backup_usage_array:
            backup_usage['guid'] = guid
            backup_usage['timestamp'] = timestamp
            backup_usage['schema_version'] = schema_version
        c42api.write_json_splunk(sys.stdout, backup_usage_array)


if __name__ == '__main__':
    _run()
