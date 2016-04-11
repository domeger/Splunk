"""
A module with common functions and variables for Splunk-related
scripts.
"""

# pylint: disable=superfluous-parens, import-error

import os
import sys
import time
from getpass import getpass

import splunk.auth as auth
import splunk.entity as entity
import c42api
from c42splunk.common import CONFIG
from c42splunk.common import ANALYTICS_DIR


def setup():
    """
    Initializes basic state for script running.

    :return: The authority server and config_dictionary.
    """
    key = _session_key()
    config_dict = _config_dict(key)
    if not config_dict or not key:
        print('something went wrong.')
        sys.exit(2)
    CONFIG.initialize(key)
    server = c42api.Server(config_dict['hostname'], port=config_dict['port'],
                           username=config_dict['username'], password=config_dict['password'],
                           verify_ssl=config_dict['verify_ssl'])
    if config_dict['collect_analytics']:
        c42api.common.analytics.OUTPUT_DIRECTORY = ANALYTICS_DIR
    log_file = os.path.join(app_home(), 'log', 'code42.log')
    c42api.set_log_file(log_file)
    return server, config_dict

def app_home():
    """
    :return: The location of the root directory of the Code42 Splunk app.
    """
    return os.path.join(CONFIG.splunk_home, 'etc', 'apps', 'code42')


def _session_key():
    """
    :return: A session key for calls to Splunk functions.
    """
    if os.isatty(sys.stdout.fileno()):
        print('Script running outside of splunkd process. Getting new sessionKey.')
        splunk_username = raw_input('Splunk Username: ')
        splunk_password = getpass('Splunk Password: ')
        key = auth.getSessionKey(splunk_username, splunk_password)
    else:
        key = sys.stdin.readline().strip()

    if not key:
        sys.stderr.write("Did not receive a session key from splunkd. Please enable passAuth in inputs.conf")

    return key


def _config_dict(session_key, attempt=0):
    """
    :param session_key: A session key for calls to Splunk functions.
    :param attempt:     The number of the attempt to get the dictionary.
                         Defaults to 0.
    :return:            A dictionary containing Splunk config info.
    """
    if attempt > 19 or not session_key:
        return {}

    try:
        # list all credentials
        password_entities = entity.getEntities(['admin', 'passwords'], namespace='code42',
                                               owner='nobody', sessionKey=session_key)
        config_console_entities = entity.getEntities(['code42', 'config', 'console'], namespace='code42',
                                                     owner='nobody', sessionKey=session_key)
        config_script_entities = entity.getEntities(['code42', 'config', 'script'], namespace='code42',
                                                    owner='nobody', sessionKey=session_key)
    except Exception as exception:
        raise Exception("Could not get code42 credentials from splunk. Error: %s" % (str(exception)))

    config = {}
    try:
        result = [item for _, item in password_entities.items() if 'username' in item and 'clear_password' in item][0]
        config['username'] = result['username']
        config['password'] = result['clear_password']

        result = [item for _, item in config_console_entities.items() if 'hostname' in item and 'port' in item][0]
        config['hostname'] = result['hostname']
        config['port'] = result['port']
        config['verify_ssl'] = result['verify_ssl'] == 'true'
        config['collect_analytics'] = result['collect_analytics'] == 'true'

        result = [item for _, item in config_script_entities.items() if 'devices' in item][0]
        config['devices'] = result['devices']
    except IndexError:
        pass

    keys = ['username', 'password', 'hostname', 'verify_ssl', 'port', 'devices']
    all_in_config = all([(key in config) for key in keys])
    if not all_in_config:
        time.sleep(1)
        return _config_dict(session_key, attempt + 1)
    else:
        return config
