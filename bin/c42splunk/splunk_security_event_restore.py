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
A wrapper script around c42api.security_event_restore that prints out
security detection events to stdout. This is intended to be called by Splunk.
"""
# pylint: disable=import-error, relative-import
import os
import sys
import json
from datetime import datetime

from common import splunk_common as common
import c42api


def _try_read_cursor(cursor_path):
    """
    If cursor exists at path, read it and return the value. Otherwise do nothing.

    :param cursor_path: Path to find cursor
    :return:            dictionary (of {guid-> "guid:event_uid"}) read from
                         cursor file
    """
    if not os.path.exists(cursor_path):
        return None
    with open(cursor_path, 'r') as cursor_file:
        return json.load(cursor_file)


def _write_cursor(cursor_path, cursor_value):
    """
    Write value to cursor file, even if it doesn't exist.

    :param cursor_path:  Where to find/create cursor file
    :param cursor_value: Value to write to cursor file

    """
    with open(cursor_path, 'w+') as cursor_file:
        json.dump(cursor_value, cursor_file)


def _run():
    """
    Run through Splunk
    """
    server, config_dict = common.setup()
    events_dir = os.path.join(common.app_home(), 'events')
    cursor_path = os.path.join(events_dir, 'security-lastRun')
    if not os.path.exists(events_dir):
        os.makedirs(events_dir)

    devices = config_dict['devices']

    device_guids = c42api.devices(server, devices)

    cursors_dict = _try_read_cursor(cursor_path)
    event_filters = []
    for device_guid in device_guids:
        try:
            cursor = cursors_dict[device_guid]
            event_filter = c42api.create_filter_by_cursor(cursor)
            event_filters.append(event_filter)
        except (KeyError, TypeError):
            event_filter = c42api.create_filter_by_utc_datetime(datetime.utcfromtimestamp(0), datetime.utcnow())
            event_filters.append(event_filter)

    guids_and_filters = zip(device_guids, event_filters)

    cursors_dict = cursors_dict if cursors_dict else {}
    for guid, cursor, detection_events in c42api.fetch_detection_events(server, guids_and_filters):
        if not cursor or not detection_events:
            continue
        cursors_dict[guid] = cursor

        c42api.write_json_splunk(sys.stdout, detection_events)

    _write_cursor(cursor_path, cursors_dict)

if __name__ == '__main__':
    _run()
