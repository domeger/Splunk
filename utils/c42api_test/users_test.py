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
Tests for the Users module in the c42api module
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
def test_fetch_fetch_users(username1, username2):
    """Test to make sure the users fetch behaves as expected"""
    body1 = {'data': {'users': [{'userId': 1, 'username': username1}]}}
    body2 = {'data': {'users': [{'userId': 2, 'username': username2}]}}
    httpretty.register_uri(httpretty.GET, 'http://test.com:7777/api/User',
                           responses=[
                               httpretty.Response(body=json.dumps(body1), status=200),
                               httpretty.Response(body=json.dumps(body2), status=200),
                               httpretty.Response(body='{}', status=200),
                           ])
    user_id = 1
    # pylint: disable=protected-access
    for user in c42api.fetch_users(basic_server()):
        assert 'userId' in user
        assert 'username' in user
        assert 'schema_version' in user
        assert user['schema_version'] == c42api.users.SCHEMA_VERSION
        assert user['userId'] == user_id
        if user_id == 1:
            assert user['username'] == username1
        if user_id == 2:
            assert user['username'] == username2
        user_id += 1
    assert user_id == 3


@test_lib.warning_to_null
@httpretty.activate
def test_fetch_no_fetch_users():
    """Test behavior of users fetch with no results"""
    httpretty.register_uri(httpretty.GET, 'http://test.com:7777/api/User',
                           responses=[
                               httpretty.Response(body='{}', status=200),
                           ])
    # pylint: disable=protected-access
    for user in c42api.fetch_users(basic_server()):
        assert user is None
        assert False


if __name__ == '__main__':
    test_lib.run_all_tests()
