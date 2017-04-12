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
A script for fetching security detection events
"""

# pylint: disable=import-error

import re
import sys
import os
import json
from Queue import Queue
from datetime import datetime
import c42api

from c42api.common.thread_pool import ThreadPool
from c42api.common.atomic_counter import AtomicCounter
from c42api.common import resources
from c42api.common import logging_config
import c42api.storage_server as fetch_storage
from c42api.common import analytics
from requests import HTTPError, RequestException

LOG = logging_config.get_logger(__name__)
SCHEMA_VERSION = 1


@analytics.with_lock
def log_analytics(**kwargs):
    """
    Passes on anything to be logged for analytics.
    """
    analytics.write_json_analytics(__name__, kwargs, result_limit=10)


def _fetch_detection_events(server, plan_uid, event_filter):
    """
    Fetch security detection events for a given plan_uid

    :raise                  HTTPError: If the request fails
    :param server:          The Server object
    :param plan_uid:        Plan to get detection events from
    :param event_filter:    Filter to use when downloading events
    :return:                returns a tuple of the cursor string, the list of
                             detection events, and whether the request was successful
                              -> (cursor_string, detection_events, request_successful)
    """
    LOG.info("Getting detection events from server %s for planUid %s with eventFilter %s", str(server), str(plan_uid),
             str(event_filter))
    assert ('minTs' in event_filter and 'maxTs' in event_filter) or 'cursor' in event_filter
    params = event_filter
    params['planUid'] = plan_uid
    params['incFiles'] = True
    try:
        response = server.json_from_response(server.get(resources.SECURITY_DETECTION_EVENTS, params=params))
    except RequestException:
        # If we fail to get the page of events successfully, return empty cursor, events, and False.
        LOG.exception(
            "Failed to get detection events from server %s for planUid %s with eventFilter %s. Please ensure the server is online",
            str(server),
            str(plan_uid),
            str(event_filter))
        return None, None, False
    try:
        return response['data']['cursor'], response['data']['securityDetectionEvents'], True
    except KeyError:
        LOG.debug("There was an error parsing the response. PlanUid: %s", str(plan_uid))
        return None, None, False


def _fetch_security_plan(server, device_guid):
    """
    Get plan with planType == 'SECURITY' for a device.
    Should only be one per device

    :raise              HTTPError: If the request fails
    :param server:      The Server object
    :param device_guid: Device to get plan for
    :return:            A single plan
    """

    params = {'sourceComputerGuid': device_guid}
    response = server.json_from_response(server.get(resources.PLAN, params=params))
    try:
        plans = [x for x in response['data'] if x['planType'].lower() == 'security']
        if len(plans) > 1:
            LOG.warn("Device %d had more than 1 security plan. Returning first one", device_guid)
        return plans[0]
    except (KeyError, IndexError):
        return None


def _append_schema_version(detection_event):
    """
    Read the function name
    """
    detection_event['schema_version'] = SCHEMA_VERSION


def _unbatch_files_in_events(detection_events):
    """
    Convert a list of batched detection events into a list of single-file
    detection events.

    Detection events can be batched, wherein a single event (for example,
    a PERSONAL_CLOUD_FILE_ACTIVITY event) may have an array of multiple file
    dictionaries. We do not want this structure when sending the events to
    another program or directly to a user. Hence, we will send individual
    events for each file.

    :param detection_events: A list of detection event dictionaries that may
                              or may not have a files list in them.
    :return:                 A list of detection events each containing
                              information about at most one file. (There may
                              be no file information.)
    """
    unbatched_events = []
    for detection_event in detection_events:
        try:
            files_list = detection_event["files"]
            for file_dict in files_list:
                unbatched_event = _copy_detection_event(detection_event)
                unbatched_event["file"] = file_dict
                unbatched_event["timestamp"] = file_dict["detectionTimestamp"]
                unbatched_events.append(unbatched_event)
        except (KeyError, TypeError):
            unbatched_events.append(detection_event)

    LOG.debug("UNBATCHING DONE:")
    return unbatched_events


# Manual implementation of copy.deepCopy(detectionEvent) to improve efficiency of the unbatching algorithm.
# The keynames were taken directly from the possible outputs of SecurityDetectionEventResource
# notice that fileStats, files, timestamp are omitted. This is intentional, as they are not needed by Splunk / are overridden.
def _copy_detection_event(originalDetectionEvent):
    try:
        newEvent = {}
        _put_if_exists("deviceAddress", newEvent, originalDetectionEvent)
        _put_if_exists("deviceGuid", newEvent, originalDetectionEvent)
        _put_if_exists("deviceRemoteAddress", newEvent, originalDetectionEvent)
        _put_if_exists("eventType", newEvent, originalDetectionEvent)
        _put_if_exists("eventUid", newEvent, originalDetectionEvent)
        _put_if_exists("formattedTimestamp", newEvent, originalDetectionEvent)
        _put_if_exists("ruleName", newEvent, originalDetectionEvent)
        _put_if_exists("schema_version", newEvent, originalDetectionEvent)
        _put_if_exists("userUid", newEvent, originalDetectionEvent)
        _put_if_exists("version", newEvent, originalDetectionEvent)
        _put_if_exists("detectionDevice", newEvent, originalDetectionEvent)
        _put_if_exists("cloudStorageProvider", newEvent, originalDetectionEvent)
        _put_if_exists("processName", newEvent, originalDetectionEvent)
        _put_if_exists("processOwner", newEvent, originalDetectionEvent)
        _put_if_exists("restoreId", newEvent, originalDetectionEvent)
        _put_if_exists("restoreType", newEvent, originalDetectionEvent)
        _put_if_exists("status", newEvent, originalDetectionEvent)
        _put_if_exists("requestingUserId", newEvent, originalDetectionEvent)
        _put_if_exists("sourceGuid", newEvent, originalDetectionEvent)
        _put_if_exists("targetGuid", newEvent, originalDetectionEvent)
        _put_if_exists("nodeGuid", newEvent, originalDetectionEvent)
        _put_if_exists("completedDate", newEvent, originalDetectionEvent)
        _put_if_exists("formattedCompletedDate", newEvent, originalDetectionEvent)
        _put_if_exists("startDate", newEvent, originalDetectionEvent)
        _put_if_exists("formattedStartDate", newEvent, originalDetectionEvent)
        _put_if_exists("totalBytes", newEvent, originalDetectionEvent)
        _put_if_exists("totalFiles", newEvent, originalDetectionEvent)
        _put_if_exists("problemCount", newEvent, originalDetectionEvent)
        _put_if_exists("failedChecksumCount", newEvent, originalDetectionEvent)

        return newEvent
    except Exception as e:
        LOG.exception("Manual KeyMapping has failed")


def _put_if_exists(fieldName, newEvent, oldEvent):
    if oldEvent.get(fieldName) != None: newEvent[fieldName] = oldEvent.get(fieldName)
    return None


# pylint: disable=invalid-name
def _fetch_detection_events_for_device(authority, device_guid, detection_event_filter, cursor_dict):
    """
    Returns unbatched detection events and the corresponding min_timestamp string (ISO format)
    for the target device. 
    The detection events are gathered by sequentially requesting a page of events from the server.
    An empty 'next_cursor' means that there are no more pages to get.

    :param authority:               A Server object to make the API call to
    :param device_guid:             Device to retrieve events for
    :param detection_event_filter:  Filter to use when pulling detection events
    :param cursor_dict:             A dictionary of deviceGuid -> cursor. This dictionary is used
                                    to store the latest cursor returned before failing to retrieve the
                                    next page of events. This allows us to restart from the proper place
                                    next time the script runs (in the event a server goes down part way through).
    :return:                        returns a tuple of the nextMinTimestamp and the list of
                                     detection events -> (next_min_timestamp, detection_events)
    """
    event_count_for_device = 0
    try:
        security_plan = _fetch_security_plan(authority, device_guid)
    except RequestException:
        LOG.exception(
            "Unable to retrieve securityPlan for deviceGuid %s, from authority %s. Please ensure the authority is online",
            str(device_guid),
            str(authority))
        security_plan = None
    if not security_plan:
        LOG.info("No security plan found for device: %s", str(device_guid))
        return None, 0, cursor_dict
    LOG.debug("Found security plan")
    for storage_server, plan_uid in fetch_storage.storage_servers(authority, [security_plan['planUid']], device_guid):
        page_count = 0

        if not storage_server:
            LOG.info("No storage servers found were found for plan %s", str(plan_uid))
            return None, event_count_for_device, cursor_dict

        # Finding a cursor in the dictionary implies that the last time the script ran, this device was only able to get
        # some of its pages of events, due to issues talking to the Code42 server(s). Start with the cursor form the last
        # successful request. Also, remove the cursor from dictionary. If this request fails, it will be re-added later on.
        cursor_from_interrupt_file = cursor_dict.pop(device_guid, None)
        if cursor_from_interrupt_file:
            detection_event_filter['cursor'] = cursor_from_interrupt_file
            LOG.info(
                "Using cursor from security-interrupted-lastCursor to get page that previously failed to be retrieved. Cursor: %s deviceGuid: %s",
                str(cursor_from_interrupt_file), str(device_guid))

        # Retrieve pages of events until an empty cursor is returned, signifying we have gotten the last page of events,
        # or a request for a page fails.
        while True:
            next_cursor, unbatched_event_page, request_successful = _get_page_of_events_from_server(storage_server,
                                                                                                    plan_uid,
                                                                                                    detection_event_filter)
            event_count_for_device += len(unbatched_event_page)
            page_count = page_count + 1

            # If the previous request was NOT successful, we need to store the cursor used in that request to the cursor_file.
            # Otherwise, we will not be able to re-try getting the page of events next time the script runs. If no cursor was used
            # we must have failed while requesting the first page. Do not store a cursor, as next time we will attempt to get the
            # first page again.
            if not request_successful and detection_event_filter.get('cursor'):
                cursor = detection_event_filter.get('cursor')
                cursor_dict[device_guid] = cursor

                LOG.debug(
                    "Page %d was not retrieved successfully. Storing cursor: %s in security-interrupted-lastCursor for deviceGuid: %s",
                    page_count, str(cursor), str(device_guid))

            # Stdout here so that we don't need to save all of the detection events for a single device.
            # After this point this page of events is 'in the splunk app'
            # NOTE: this must be done single-threaded
            c42api.write_json_splunk(sys.stdout, unbatched_event_page)

            if not next_cursor and request_successful:
                LOG.info("All pages of events retrieved for plan: %s, from server %s, total pages retrieved: %d",
                         plan_uid, storage_server, page_count)
                # This value will be used as the event_filter['minTs'] value the next time Splunk retrieves events for this device.
                # the value will be stored in a local cache until then.
                next_min_ISO_timestamp = detection_event_filter['maxTs']

                return next_min_ISO_timestamp, event_count_for_device, cursor_dict
            elif not next_cursor:
                LOG.info(
                    "Unable to get all pages of events for plan: %s, from server %s. The next time script runs, we will try to retrieve page %d again.",
                    plan_uid, str(storage_server), page_count)
                return None, event_count_for_device, cursor_dict

            # Replacing the previous cursor with the next_cursor allows us to get the next page of events with our next request.
            detection_event_filter['cursor'] = next_cursor

    return detection_event_filter['minTs'], event_count_for_device, cursor_dict


def _get_page_of_events_from_server(storage_server, plan_uid, detection_event_filter):
    next_cursor, detection_events, request_successful = _fetch_detection_events(storage_server, plan_uid,
                                                                                detection_event_filter)
    if next_cursor and detection_events:
        for detection_event in detection_events:
            _append_schema_version(detection_event)
        LOG.debug(
            "Starting file unbatcher for page:: num detectionEvents being unbatched: %d plan %s",
            len(detection_events), str(plan_uid))
        return next_cursor, _unbatch_files_in_events(detection_events), request_successful
    LOG.debug("LAST PAGE OF EVENTS:: for planUid %s", str(plan_uid))
    return None, [], request_successful


def create_filter_by_utc_datetime(min_datetime, max_datetime):
    """
    Create a minTs, maxTs filter. Datetime object must be in utc time. API contract requires it.
    """

    if min_datetime > max_datetime:
        raise ValueError("min_datetime > max_datetime")

    try:
        # Basic Datetime object does not create the correctly formatted timestamp
        # necessary when making SecurityDetectionEvents API calls. That is why we
        # have the custum time formatter.
        return {'minTs': min_datetime.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                'maxTs': max_datetime.strftime("%Y-%m-%dT%H:%M:%S.000Z")}
    except ValueError:
        LOG.error("Failed to create event_filter")
        return None


def create_filter_by_iso_minTs_and_now(iso_minTs):
    """
    Create a minTs, maxTs filter. iso_minTs must be in the correct ISO format.
    maxTs is always set to 'now' in utc.
    """
    if not iso_minTs:
        raise ValueError("is_minTs must be supplied")
    if not re.match("^[0-9]{4}\-[0-9]{2}\-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z", iso_minTs):
        # the regex here matches the expected ISO date time format which the SecurityDetectionEventResource expects
        # for minTs / maxTs. Expected format example: 2017-04-18T21:50:06.000Z
        LOG.warn("MinTs from security-lastRun is not in the correct format: %s", iso_minTs)
        raise ValueError("Invalid iso_minTs value. supplied value = " + iso_minTs)

    try:
        # Basic Datetime object does not create the correctly formatted timestamp
        # necessary when making SecurityDetectionEvents API calls. That is why we
        # have the custum time formatter.
        return {'minTs': iso_minTs,
                'maxTs': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")}
    except ValueError:
        LOG.error("Failed to create event_filter")
        return None


def create_filter_by_cursor(cursor):
    """
    Create a cursor filter
    """
    # cursor is two positives longs, plan_uid and event_uid, seperated by a colon
    if not re.match("(^[0-9]{1,19}:[0-9]{1,19}$)", cursor):
        raise ValueError("Invalid cursor format")

    return {'cursor': cursor}


def _try_read_cursor(cursor_file_path):
    """
    If timestamp exists at path, read it and return the value. Otherwise do nothing.

    :param timestamp_path: Path to find timestamp
    :return: dictionary (of {guid-> "<planUid>:<eventUid>") read from
             cursor file
    """
    if not os.path.exists(cursor_file_path):
        return None
    with open(cursor_file_path, 'r') as cursor_file:
        return json.load(cursor_file)


def _write_cursor(cursor_file_path, cursor_dict):
    """
    Write value to timestamp file, even if it doesn't exist.

    :param cursor_file_path:  Where to find/create cursor file
    :param cursor_dict: Value to write to cursor file. This value is a dict of deviceGuid -> cursor
    """
    with open(cursor_file_path, 'w+') as cursor_file:
        json.dump(cursor_dict, cursor_file)


def fetch_detection_events(authority, guid_and_filter_list, cursor_file_path):
    """
    Returns an iterable (specifically a generator) containing json objects
    that represent all security detection events for a specific device guid.
    (all pages of events for the deviceGuid)

    :param authority:             A Server object to make the API call to
    :param guid_and_filter_list:  A pre-zipped list of (device_guid,
                                  event_filter)
    :param cursor_file_path:      The path to the file where we will save currentCursor in 
                                  case of loosing connection to server during page retrieval.
    :return:                      returns a tuple of the device_guid, the next_min_ISO_timestamp
                                  string and a count of how many detection events were found.
                                  (device_guid, next_min_ISO_timestamp, detection_event_count)
    """

    start_time = datetime.now().isoformat()
    device_guids = [item[0] for item in guid_and_filter_list]
    LOG.info("Begin fetching detection events devices:%s", str(device_guids))

    cursor_dict = _try_read_cursor(cursor_file_path)
    cursor_dict = cursor_dict if cursor_dict else {}

    total_event_count = 0
    for device_guid, detection_event_filter in guid_and_filter_list:
        # Get detection events for device guid and add to
        # list of all detection events
        #
        # The _fetch_detection_events_for_device() call could return nothing but our exit condition
        # expects that every task will return some result so no matter what, we have to output
        # a result to the result_queue.

        LOG.info("Fetching detection events for %s", str(device_guid))
        next_min_ISO_timestamp = None
        detection_event_count = 0
        try:
            next_min_ISO_timestamp, detection_event_count, cursor_dict = _fetch_detection_events_for_device(authority,
                                                                                                            device_guid,
                                                                                                            detection_event_filter,
                                                                                                            cursor_dict)
            LOG.info("Got %d detection events for computerGuid %s", detection_event_count, str(device_guid))
        except RequestException:
            LOG.exception("Failure when fetching detection events for device %s", str(device_guid))

        total_event_count += detection_event_count
        yield (device_guid, next_min_ISO_timestamp)

    LOG.info("Finished fetching detection events for devices. Got %d events total, for the Devices: %s",
             total_event_count,
             str(device_guids))
    _write_cursor(cursor_file_path, cursor_dict)

    end_time = datetime.now().isoformat()
    log_analytics(start_time=start_time,
                  end_time=end_time,
                  event_count=total_event_count)
