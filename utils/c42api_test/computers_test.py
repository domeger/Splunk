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
Tests for the Computers module in the c42api module
"""

import json
import httpretty
from hypothesis import given, Settings
import hypothesis.strategies as strat

import c42api
from c42api_test import test_lib


def basic_server():
    """
    :return: A general purpose server object
    """
    return c42api.Server('test.com', '7777', 'testname', 'testword')


@test_lib.warning_to_null
@httpretty.activate
@given(strat.text(), strat.text(), settings=Settings(max_examples=50))
def test_fetch_all_devicess(osname1, osname2):
    """Test to make sure the computers fetch behaves as expected"""
    body1 = {'data': {'computers': [{'computerId': 1, 'osName': osname1}]}}
    body2 = {'data': {'computers': [{'computerId': 2, 'osName': osname2}]}}
    httpretty.register_uri(httpretty.GET, 'http://test.com:7777/api/Computer',
                           responses=[
                               httpretty.Response(body=json.dumps(body1), status=200),
                               httpretty.Response(body=json.dumps(body2), status=200),
                               httpretty.Response(body='{}', status=200),
                           ])
    computer_id = 1
    # pylint: disable=protected-access
    params = {'active': 'true',
              'incBackupUsage': False,
              'incHistory': False}
    for computer in c42api.fetch_computers(basic_server(), params, insert_schema_version=True):
        assert 'computerId' in computer
        assert 'osName' in computer
        assert 'schema_version' in computer
        assert computer['schema_version'] == c42api.computers.SCHEMA_VERSION
        assert computer['computerId'] == computer_id
        if computer_id == 1:
            assert computer['osName'] == osname1
        if computer_id == 2:
            assert computer['osName'] == osname2
        computer_id += 1
    assert computer_id == 3


@test_lib.warning_to_null
@httpretty.activate
def test_fetch_no_devices():
    """Test behavior of computers fetch with no results"""
    httpretty.register_uri(httpretty.GET, 'http://test.com:7777/api/Computer',
                           responses=[
                               httpretty.Response(body='{}', status=200),
                           ])
    # pylint: disable=protected-access
    for computer in c42api.fetch_computers(basic_server()):
        assert computer is None
        assert False


if __name__ == '__main__':
    test_lib.run_all_tests()
