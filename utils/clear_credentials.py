#!/bin/echo Usage: splunk cmd python clear_credentials.py

# File: clear_credentials.py
# Author: Hank Brekke
# Last Modified: 06/23/2015
#
# Clears Code42 Server login credentials from the Splunk app, allowing
# new credentials to be saved using the Setup screen.
#
# Usage: splunk cmd python clear_credentials.py
#

import os
import sys
import httplib
import base64 as encode
import getpass as password

from splunk.clilib import cli_common as cli

SPLUNK_HOME = os.environ['SPLUNK_HOME']
APP_CONFIG = os.path.join(SPLUNK_HOME, 'etc', 'apps', 'code42', 'local', 'app.conf')

print('')

config = cli.getConfStanzas('app')
credential_keys = []
for key, value in config.iteritems():
    if key.startswith('credential'):
        credential_keys.append(key)

if len(credential_keys) == 0:
    print('All Code42 credentials have already been cleared.')
    print('')
    sys.exit(0)

for credential_key in credential_keys:
    credentials = credential_key.split(':')
    code42_username = credentials[2]
    print('Clearing Splunk Code42 credentials for ' + code42_username + '.')

print('')

splunk_username = raw_input('Splunk Username: ')
splunk_password = password.getpass('Splunk Password: ')
print('')

userAndPass = encode.b64encode(splunk_username + ':' + splunk_password).decode("ascii")
headers = { 'Authorization' : 'Basic %s' %  userAndPass }

for credential_key in credential_keys:
    credentials = credential_key.split(':')
    code42_username = credentials[2]

    conn = httplib.HTTPSConnection('localhost', 8089)
    conn.request('DELETE', '/servicesNS/nobody/code42/storage/passwords/%3A' + code42_username + '%3A', headers=headers)
    resp = conn.getresponse()

    if resp.status == 401:
        raise Exception('Splunk username or password is invalid, or does not have valid permission.')
    elif resp.status != 200:
        raise Exception('Error ' + resp.status + ' deleting user credentials.')

    print('Successfully cleared ' + code42_username + ' credentials.')

print('All Code42 credentials have been cleared.')
print('')
