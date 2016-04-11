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
