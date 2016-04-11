"""
A wrapper script the users module in c42api that prints out data to Splunk
lookup tables. This is intended to be called by Splunk.
"""

# pylint: disable=relative-import, import-error
import os

from common import splunk_common as common
import c42api
from splunk_utils import splunk_lookup_table

TIME_KEY = 'modificationDate'
USER_KEYS_TO_IGNORE = ['modificationDate']
USER_UID_KEY = 'userUid'


def _run():
    """
    The script's body. Creates/Updates Splunk user lookup table.
    """
    app_home = common.app_home()

    lookups_dir = os.path.join(app_home, "lookups")
    old_user_lookup_table = os.path.join(lookups_dir, "user_lookup.csv")
    tmp_user_lookup_table = os.path.join(lookups_dir, "user_lookup_tmp.csv")

    if not os.path.exists(lookups_dir):
        os.makedirs(lookups_dir)

    server, _ = common.setup()

    # write user lookup table
    user_results = c42api.fetch_users(server)
    splunk_lookup_table.write_lookup_table(old_user_lookup_table, tmp_user_lookup_table, user_results,
                                           USER_UID_KEY, USER_KEYS_TO_IGNORE, TIME_KEY)


if __name__ == '__main__':
    _run()
