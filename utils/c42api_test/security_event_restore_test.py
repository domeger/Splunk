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
Test aspects of the security event restore script
"""
# Disabling 'unused-argument' because of all the mock functions
# Disabling 'invalid-name' because of the length of the test functions' names
# pylint: disable=protected-access, import-error, unused-argument, invalid-name
from datetime import datetime
import c42api
from c42api_test import test_lib
import random
import sys


def basic_server():
    """
    :return: A general purpose server object
    """
    return c42api.Server('test.com', '7777', 'testname', 'testword')

def generate_cursor():
    """
    Generate a properly formatted cursor string
    """
    return "{0}:{1}".format(random.randint(0, sys.maxint), random.randint(0, sys.maxint))

def generate_detection_events(num_events):
    """
    Generate a dictionary representing a  detection event
    """
    events = []
    for i in range(num_events):
        events.append("Event{0}".format(i))
    return events

def create_event_filter_by_datetime_test():
    """
    Test that we create a correct filter from a datetime pair
    """
    min_datetime = datetime.fromtimestamp(1231)
    max_datetime = datetime.fromtimestamp(123123)
    expected_min_ts_result = min_datetime.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    expected_max_ts_result = max_datetime.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    event_filter = c42api.create_filter_by_utc_datetime(min_datetime, max_datetime)
    assert event_filter == {'minTs':expected_min_ts_result, 'maxTs':expected_max_ts_result}

    try:
        c42api.create_filter_by_utc_datetime(max_datetime, min_datetime)
        assert False
    except ValueError:
        pass


def create_event_filter_by_cursor_test():
    """
    Test that we create a correct event filter from an existing cursor
    """
    valid_cursor = "1234567890:1234567890"
    invalid_cursors = ["1234567890:",
                       ":1234567890",
                       ":",
                       "",
                       " ",
                       "1234567890a:1234567890",
                       "1234567890:a1234567890",
                       "1234567890a:a1234567890",
                       "1234567890::1234567890"
                      ]

    event_filter = c42api.create_filter_by_cursor(valid_cursor)
    assert event_filter == {'cursor':valid_cursor}

    for invalid_cursor in invalid_cursors:
        try:
            c42api.create_filter_by_cursor(invalid_cursor)
            assert False
        except ValueError:
            pass

@test_lib.reload_modules_post_execution(c42api)
def fetch_detection_events_test():
    """
    Test we fetch detection events in an expected way
    """
    cursor_string = generate_cursor()
    device_guids = [1, 2, 3]
    event_filters = ['word'] * 3
    guids_and_filters = zip(device_guids, event_filters)
    expected_results = {}
    for device_guid in device_guids:
        expected_results[str(device_guid)] = [
            'word',
            generate_detection_events(random.randint(1, 20))
        ]

    event_filter = c42api.create_filter_by_cursor(cursor_string)

    def mock_fetch_detection_events_for_device(server, device_guid, event_filter):
        """
        Mock Func
        """
        return expected_results[str(device_guid)][0], expected_results[str(device_guid)][1]

    def mock_fetch_security_plan(server, device_guid):
        """
        Mock Func
        """
        return {'planUid':12312123}

    def mock_storage_servers(authority, plan_uids=None, device_guid=None):
        """
        Mock Func
        """
        return basic_server(), 1232

    c42api.security_event_restore._fetch_detection_events_for_device = mock_fetch_detection_events_for_device
    c42api.security_event_restore._fetch_security_plan = mock_fetch_security_plan
    c42api.security_event_restore.fetch_storage.storage_servers = mock_storage_servers

    for device_guid, cursor, detection_events in c42api.fetch_detection_events(basic_server(), guids_and_filters):
        assert (device_guid in device_guids
                and cursor == expected_results[str(device_guid)][0]
                and detection_events == expected_results[str(device_guid)][1])


if __name__ == '__main__':
    test_lib.run_all_tests()
