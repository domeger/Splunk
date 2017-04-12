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
import json
from datetime import datetime

from common import splunk_common as common
import c42api


def _try_read_timestamp(timestamp_path):
    """
    If timestamp exists at path, read it and return the value. Otherwise do nothing.

    :param timestamp_path: Path to find timestamp
    :return: dictionary (of {guid-> "<timestamp in ISO format>"}) read from
             timestamp file
    """
    if not os.path.exists(timestamp_path):
        return None
    with open(timestamp_path, 'r') as timestamp_file:
        return json.load(timestamp_file)


def _write_min_timestamps(next_minTs_path, timestamp_dict):
    """
    Write value to timestamp file, even if it doesn't exist.

    :param next_minTs_path:  Where to find/create timestamp file
    :param timestamp_dict:   Dict holding Value to write to minTs file. This value is dictionary entries 
                             of deviceGuid -> string in ISO format example: '2017-04-11T19:11:40.000Z'
    """
    with open(next_minTs_path, 'w+') as minTs_file:
        json.dump(timestamp_dict, minTs_file)


def _run():
    """
    Run through Splunk. This is how the Splunk app gathers security detection events from the Code42 server(s).
    For each user, we gather all events for 
    """
    server, config_dict = common.setup()
    events_dir = os.path.join(common.app_home(), 'events')
    # The file at 'minTs_file_path' holds the 'min timestamp' to be used for a particular device the next time
    # the script runs. This is updated IFF all pages are gathered for a particular device during a single run of the script.
    minTs_file_path = os.path.join(events_dir, 'security-lastRun')
    # The file at 'cursor path' is used to hold the 'latest cursor' for a particular plan on a page by page basis.
    # i.e. every time we finish retrieving a plan, we save the new 'latest cursor' to ensure that we can restart
    # from the correct page in the case the connection to the C42 server goes down before we retrieve all pages.
    cursor_path = os.path.join(events_dir, 'security-interrupted-lastCursor')
    if not os.path.exists(events_dir):
        os.makedirs(events_dir)

    devices = config_dict['devices']
    device_guids = c42api.devices(server, devices)

    timestamp_dict = _try_read_timestamp(minTs_file_path)
    event_filters = []
    for device_guid in device_guids:
        try:
            minTs = timestamp_dict[device_guid]
            event_filter = c42api.create_filter_by_iso_minTs_and_now(minTs)
            event_filters.append(event_filter)
        except (KeyError, TypeError):
            event_filter = c42api.create_filter_by_utc_datetime(datetime.utcfromtimestamp(0), datetime.utcnow())
            event_filters.append(event_filter)

    guids_and_filters = zip(device_guids, event_filters)

    timestamp_dict = timestamp_dict if timestamp_dict else {}
    for guid, new_minTs in c42api.fetch_detection_events(server, guids_and_filters, cursor_path):
        if not new_minTs:
            continue
        timestamp_dict[guid] = new_minTs

    _write_min_timestamps(minTs_file_path, timestamp_dict)


if __name__ == '__main__':
    _run()
