#!/bin/echo Usage: splunk cmd python clear_credentials.py

# File: clear_credentials.py
# Author: Hank Brekke
#
# Clears Code42 Server login credentials from the Splunk app, allowing
# new credentials to be saved using the Setup screen.
#
# Usage: splunk cmd python clear_credentials.py
#

import os
import sys
import getpass as password

import splunk.entity as entity
import splunk.auth as auth

SPLUNK_HOME = os.environ['SPLUNK_HOME']
APP_CONFIG = os.path.join(SPLUNK_HOME, 'etc', 'apps', 'code42', 'local', 'app.conf')

print('')

print('This script will remove all saved credentials from the Code42 app.')
print('You will confirm this before they are removed.')
print('')

splunk_username = raw_input('Splunk Username: ')
splunk_password = password.getpass('Splunk Password: ')
print('')

sessionKey = auth.getSessionKey(splunk_username, splunk_password)

passwordEntities = entity.getEntities(['admin', 'passwords'], namespace='code42', owner='nobody', sessionKey=sessionKey)

# The permission "Sharing for config file-only objects" adds other app's
# credentials to this list. We need to make sure we filter down to only
# the username/password stored by the Code42 app.
#
# https://github.com/code42/Splunk/issues/2
def _password_match(credential):
    """Determine whether a credential matches this app namespace"""
    try:
        return credential['eai:acl']['app'] == 'code42'
    except AttributeError:
        return False

passwords = {i:x for i, x in passwordEntities.items() if _password_match(x)}

if len(passwords) == 0:
    print('All Code42 credentials have already been cleared.')
    print('')
    sys.exit(0)

for name, credential in passwords.items():
    print('Found credentials for username "%s".' % credential['username'])

print('')
confirm = raw_input('To confirm deletion(s), type "DELETE": ')
print('')

if confirm.upper() != "DELETE":
    print('Aborting.')
    print('')
    sys.exit(1)

for name, credential in passwords.items():
    entity.deleteEntity(['admin', 'passwords'], name, namespace='code42', owner='nobody', sessionKey=sessionKey)

    print('Successfully cleared ' + credential['username'] + ' credentials.')

print('')
print('All Code42 credentials have been cleared.')
print('')
