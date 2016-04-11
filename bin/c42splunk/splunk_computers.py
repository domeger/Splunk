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
