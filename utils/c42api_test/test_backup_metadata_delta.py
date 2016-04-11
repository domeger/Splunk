"""Unit tests for backup_metadata_delta component in `c42script` module.

This script contains unit test code for the backup_metadata_delta component.
"""

# pylint: disable=import-error,invalid-name,protected-access

import os
import datetime
import json

import httpretty
import hypothesis

from c42api import backup_metadata_delta
from c42api.common import resources
from c42api.common.server import Server

from c42api_test import test_lib

SERVER = Server('backup_metadata_delta.test', '8378')
def _api_url(resource):
    """Get a URL using the test SERVER variable for an API resource"""
    _, url = SERVER._prep_request(resource, None)
    return url

with open(os.path.join(os.path.dirname(__file__), "data", "test_backup_metadata_delta.json")) as f:
    RESPONSE_DATA = json.load(f)

@httpretty.activate
@test_lib.disable_storage_server
@test_lib.warning_to_null
def test_calculate_delta_http_sequence():
    """
    Test the HTTP sequences used by backup_metadata_delta

    :raise AssertionError:  Extraneious API call is being made.
    :raise ConnectionError: Extraneious (unhandled) API call is being made.
    """
    minimum_date = datetime.datetime.fromtimestamp(0)
    maximum_date = datetime.datetime.now()
    device_guid = 1234

    request_history = []

    def callback_data_key_token(request, uri, headers):
        """Callback when DATA_KEY_TOKEN resource is requested"""
        request_history.append(uri)

        body = json.loads(request.body)

        assert "computerGuid" in body
        assert body["computerGuid"] == device_guid

        return 200, headers, '{"data":{"dataKeyToken":"abcd"}}'

    httpretty.register_uri(httpretty.POST, _api_url(resources.DATA_KEY_TOKEN),
                           body=callback_data_key_token, content_type='application/json')

    def callback_archive_metadata(_, uri, headers):
        """Callback when ARCHIVE_METADATA resource is requested"""
        request_history.append(uri)

        assert "idType=guid" in uri
        assert "decryptPaths=true" in uri
        assert "dataKeyToken=abcd" in uri

        return 200, headers, '{"data":[]}'

    httpretty.register_uri(httpretty.GET, _api_url([resources.ARCHIVE_METADATA, device_guid]),
                           body=callback_archive_metadata, content_type='application/json')

    delta = backup_metadata_delta.calculate_delta(SERVER, device_guid, minimum_date, maximum_date)
    delta = list(delta)

    assert len(request_history) == 2
    assert isinstance(delta, list)
    assert len(delta) is 0

@httpretty.activate
@test_lib.disable_storage_server
@test_lib.warning_to_null
@hypothesis.given(hypothesis.strategies.text())
def test_calculate_delta_event_structure(file_name):
    """
    Test the event structure of a returned event object.

    :raise AssertionError:  Events are not structured properly.
    :raise ConnectionError: Extraneious (unhandled) API call is being made.
    """
    minimum_date = datetime.datetime.fromtimestamp(0)
    maximum_date = datetime.datetime.now()
    device_guid = 1234

    metadata_response = RESPONSE_DATA["test_calculate_delta_event_structure"]
    metadata_response["data"][0]["path"] = file_name

    httpretty.register_uri(httpretty.POST, _api_url(resources.DATA_KEY_TOKEN),
                           responses=[
                               httpretty.Response(body='{"data":{"dataKeyToken":""}}', status=200)
                           ])
    httpretty.register_uri(httpretty.GET, _api_url([resources.ARCHIVE_METADATA, device_guid]),
                           responses=[
                               httpretty.Response(body=json.dumps(metadata_response),
                                                  status=200)
                           ])

    delta = backup_metadata_delta.calculate_delta(SERVER, device_guid, minimum_date, maximum_date)
    delta = list(delta)

    # Assert `delta` filtered is not empty from response.
    assert len(delta) > 0

    # Assert `event` contains all standard keys from security event.
    event = delta[0]
    assert "timestamp" in event
    assert "schema_version" in event
    assert event["schema_version"] == 1
    assert "deviceGuid" in event
    assert event["deviceGuid"] == device_guid
    assert "eventType" in event
    assert "files" in event
    assert len(event["files"]) == 1

    # Assert `event.files{}` contains all standard keys from security event.
    event_file = event["files"][0]
    assert "fileEventType" in event_file
    assert "lastModified" in event_file
    assert "fileType" in event_file
    assert "MD5Hash" in event_file
    assert "fileName" in event_file
    assert "length" in event_file
    assert "fullPath" in event_file
    assert event_file["lastModified"] == event["timestamp"]

@httpretty.activate
@test_lib.disable_storage_server
@test_lib.warning_to_null
def test_calculate_delta_filtering():
    """
    Test the datetime filtering of events after a full API response.

    :raise AssertionError:  Events are not being filtered properly.
    :raise ConnectionError: Extraneious (unhandled) API call is being made.
    """
    minimum_date = datetime.datetime(2015, 8, 14)
    maximum_date = datetime.datetime(2015, 8, 15)
    device_guid = 1234

    metadata_response = RESPONSE_DATA["test_calculate_delta_event_structure"]

    httpretty.register_uri(httpretty.POST, _api_url(resources.DATA_KEY_TOKEN),
                           responses=[
                               httpretty.Response(body='{"data":{"dataKeyToken":""}}',
                                                  status=200)
                           ])
    httpretty.register_uri(httpretty.GET, _api_url([resources.ARCHIVE_METADATA, device_guid]),
                           responses=[
                               httpretty.Response(body=json.dumps(metadata_response),
                                                  status=200)
                           ])

    delta = backup_metadata_delta.calculate_delta(SERVER, device_guid, minimum_date, maximum_date)
    delta = list(delta)

    # Assert `delta` filtered one of the two versions in the response.
    assert len(delta) == 1

if __name__ == "__main__":
    test_lib.run_all_tests()
