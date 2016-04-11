"""
Tests for the Server class in the c42api module
"""

import json
from hypothesis import given
from hypothesis import assume
import hypothesis.strategies as strat
import httpretty

from c42api.common.server import Server
import c42api_test.test_lib as test_lib


def basic_server():
    """
    :return: A general purpose server object
    """
    return Server('test.com', '7777', 'testname', 'testword')


@given(strat.text(), strat.integers(1, 65535),
       strat.text(), strat.text(),
       strat.sampled_from(['http', 'https']))
def test_init(server_address, port, username, password, protocol):
    """Test to make sure basic initialization works"""

    assume(not server_address.endswith('/'))
    assume(server_address.count(':') == 0)

    server = Server(server_address, port, username, password, protocol)
    assert server
    assert server.server_address == server_address
    assert server.port == port
    assert server.username == username
    assert server.password == password
    assert server.protocol == protocol

def test_address_parsing():
    # Implied protocol, no port
    server = Server("code42.com")
    assert server.url_name() == "https://code42.com"

    # Implied protocol, secure port
    server = Server("code42.com:4285")
    assert server.url_name() == "https://code42.com:4285"

    # Implied protocol, non-secure port
    server = Server("code42.com:4280")
    assert server.url_name() == "http://code42.com:4280"

    # Explicit protocol, no port
    server = Server("https://code42.com")
    assert server.url_name() == "https://code42.com"

    # Explicit protocol, secure port
    server = Server("https://code42.com:4285")
    assert server.url_name() == "https://code42.com:4285"

    # Explicit protocol, non-secure port
    server = Server("https://code42.com:4280")
    assert server.url_name() == "https://code42.com:4280"

    # Explicit protocol, secure port, trailing slash
    server = Server("https://code42.com:4280/")
    assert server.url_name() == "https://code42.com:4280"

    # Explicit protocol, invalid port
    server = Server("https://code42.com:428a0")
    assert server.url_name() == "https://code42.com"

    # Invalid protocol, non-secure port
    server = Server("htttps://code42.com:4280")
    assert server.url_name() == "htttps://code42.com:4280"

    # Implied protocol, secure port argument
    server = Server("code42.com", port=4285)
    assert server.url_name() == "https://code42.com:4285"

    # Implied protocol, non-secure port argument
    server = Server("code42.com", port=4280)
    assert server.url_name() == "http://code42.com:4280"

    # Explicit protocol, secure port argument
    server = Server("https://code42.com", port=4285)
    assert server.url_name() == "https://code42.com:4285"

    # Explicit protocol, non-secure port argument
    server = Server("https://code42.com", port=4280)
    assert server.url_name() == "https://code42.com:4280"

    # Explicit protocol, port, override port argument
    server = Server("https://code42.com:4285", port=4280)
    assert server.url_name() == "https://code42.com:4280"

    # Explicit protocol, port, override port argument
    server = Server("http://code42.com:4280", port=4285)
    assert server.url_name() == "http://code42.com:4285"

    # Protocol, port, override protocol argument
    server = Server("http://code42.com:4280", protocol="https")
    assert server.url_name() == "https://code42.com:4280"

    # Protocol, port, override protocol argument, override port argument
    server = Server("http://code42.com:4280", protocol="https", port=4285)
    assert server.url_name() == "https://code42.com:4285"

def test_server_ssl_setting():
    server = Server("code42.com", protocol="https")
    assert server.verify_ssl == True

    server = Server("code42.com", protocol="https", verify_ssl=False)
    assert server.verify_ssl == False

    try:
        server.verify_ssl = True
        assert False
    except AttributeError:
        pass

def test_server_address():
    """Test to make sure server_address is immutable"""
    server = basic_server()
    try:
        server.server_address = 'test'
        assert False
    except AttributeError:
        assert True


def test_port():
    """Test to make sure port is immutable"""
    server = basic_server()
    try:
        server.port = 'test'
        assert False
    except AttributeError:
        assert True


def test_username():
    """Test to make sure username is immutable"""
    server = basic_server()
    try:
        server.username = 'test'
        assert False
    except AttributeError:
        assert True


def test_password():
    """Test to make sure password is immutable"""
    server = basic_server()
    try:
        server.password = 'test'
        assert False
    except AttributeError:
        assert True


def test_protocol():
    """Test to make sure protocol is immutable"""
    server = basic_server()
    try:
        server.protocol = 'test'
        assert False
    except AttributeError:
        assert True


def test_custom():
    """Test to make sure any additional properties are mutable"""
    server = basic_server()
    server.test_prop = 'test'
    try:
        server.test_prop = 'pass'
        assert server.test_prop == 'pass'
    except AttributeError:
        assert False


@test_lib.warning_to_null
@httpretty.activate
def test_get():
    """Test to make sure get rest call behaves as expected"""
    params = {'param_one': 'value_one',
              'param_two': 'value_two'}

    def request_callback(_, uri, headers):
        """Callback function that asserts get request has proper paramters"""
        for param, value in params.items():
            assert '{}={}'.format(param, value) in uri
        return 200, headers, json.dumps({'result': 'test'})
    httpretty.register_uri(httpretty.GET, 'http://test.com:7777/api/Test',
                           body=request_callback, content_type='application/json')
    resp = basic_server().get('Test', params)
    assert Server.json_from_response(resp)['result'] == 'test'


@test_lib.warning_to_null
@httpretty.activate
def test_post():
    """Test to make sure post rest call behaves as expected"""
    pass


@test_lib.warning_to_null
@httpretty.activate
def test_put():
    """Test to make sure put rest call behaves as expected"""
    pass


@test_lib.warning_to_null
@httpretty.activate
def test_delete():
    """Test to make sure delete rest call behaves as expected"""
    pass


@given(strat.text(), strat.integers(1, 65535), strat.sampled_from(['http', 'https']))
def test_url_name(url, port, protocol):
    """Test to make sure url name generation behaves as expected"""

    assume(not url.endswith('/'))
    assume(url.count(':') == 0)

    server = Server(url, port, 'carl', 'password', protocol)

    assert server.url_name() == u'{}://{}:{}'.format(protocol, url, port)


@given(strat.text())
def test_url_name_port_exclusion(url):
    """Special case of url name generation that doesn't display ports"""

    assume(not url.endswith('/'))
    assume(url.count(':') == 0)

    server = Server(url, None, 'carl', 'password', 'http')
    print(url, server.url_name(), server.__dict__, u'{}://{}'.format('http', url))
    assert server.url_name() == u'{}://{}'.format('http', url)


def test_json_from_response():
    """Test to make sure json gets parsed correctly from bytes"""
    response = FakeResponse(b'{"thing": "result"}')
    json_resp = Server.json_from_response(response)
    assert json_resp['thing'] == 'result'


# pylint: disable=too-few-public-methods
class FakeResponse(object):
    """A dummy response object that has relevant instance variables"""
    def __init__(self, content):
        self.content = content

if __name__ == '__main__':
    test_lib.run_all_tests()
