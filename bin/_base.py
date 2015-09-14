# File: _base.py
# Author: Hank Brekke
#
# Base class for performing common Splunk actions, such as calling
# out to external Python3 or getting a sessionKey.
#

import os
import sys
import subprocess
import glob
import time
from distutils.spawn import find_executable as which
import getpass as password
import threading

import splunk.auth as auth
import splunk.entity as entity

class SplunkScript(object):
    PYTHONPATH = None
    SPLUNK_HOME = os.environ.get('SPLUNK_HOME')

    sessionKey = None
    config = None
    appHome = os.path.join(SPLUNK_HOME, 'etc', 'apps', 'code42')

    def __init__(self):
        # Path to the system Python executable on your Splunk server.
        PYTHONPATH = which("python3")

        if os.name == 'nt':
            # Try to find Python3 from it's default install location.
            possiblePaths = glob.glob("C:\Python3*") + glob.glob("C:\Program Files\Python 3*")

            for possiblePath in possiblePaths:
                possiblePython = "%s\python.exe" % possiblePath
                if os.path.exists(possiblePython):
                    PYTHONPATH = possiblePython
                    break

            if not PYTHONPATH:
                # On Windows, The `python.exe` in $PATH might still be Python 3, but this is a last resort.
                PYTHONPATH = which("python.exe")

                sys.stderr.write("Python3 may not be installed. Reverting to (potentially unstable) `%s`\n" % PYTHONPATH)

        if not PYTHONPATH:
            # We can't use `which("python")` because it will pick up on Splunk's embedded Python.
            PYTHONPATH = "/usr/bin/python"
            
            sys.stderr.write("Python3 is not installed. Reverting to (potentially unstable) default Python.\n")

        self.PYTHONPATH = PYTHONPATH

    def getSessionKey(self):
        if not self.sessionKey:
            if os.isatty(sys.stdout.fileno()):
                print('')
                print('Script running outside of splunkd process. Getting new sessionKey.')
                splunk_username = raw_input('Splunk Username: ')
                splunk_password = password.getpass('Splunk Password: ')
                print('')

                self.sessionKey = auth.getSessionKey(splunk_username, splunk_password)
            else:
                self.sessionKey = sys.stdin.readline().strip()

        if len(self.sessionKey) == 0:
            sys.stderr.write("Did not receive a session key from splunkd. " +
                            "Please enable passAuth in inputs.conf for this " +
                            "script\n")
            sys.exit(2)

        return self.sessionKey

    def getConfig(self, attempt=0):
        if not self.config and attempt < 20:
            sessionKey = self.getSessionKey()

            try:
                # list all credentials
                passwordEntities = entity.getEntities(['admin', 'passwords'], namespace='code42', owner='nobody', sessionKey=sessionKey)
                configConsoleEntities = entity.getEntities(['code42', 'config', 'console'], namespace='code42', owner='nobody', sessionKey=sessionKey)
            except Exception as e:
                raise Exception("Could not get code42 credentials from splunk. Error: %s" % (str(e)))

            config = {}

            # The permission "Sharing for config file-only objects" adds other app's
            # credentials to this list. We need to make sure we filter down to only
            # the username/password stored by the Code42 app.
            #
            # https://github.com/code42/Splunk/issues/2
            passwords = {i:x for i, x in passwordEntities.items() if 'eai:acl' in x and 'app' in x['eai:acl'] \
                                                                     and x['eai:acl']['app'] == 'code42'}
            for i, c in passwords.items():
                if 'username' in c and c['username']:
                    config['username'] = c['username']
                if 'clear_password' in c and c['clear_password']:
                    config['password'] = c['clear_password']

            for i, c in configConsoleEntities.items():
                if 'hostname' in c and c['hostname']:
                    config['hostname'] = c['hostname']
                if 'port' in c and c['port']:
                    config['port'] = c['port']

            if ('username' not in config or
                'password' not in config or
                'hostname' not in config or
                'port' not in config):

                # sleep a second, try again
                time.sleep(1)
                return self.getConfig(attempt + 1)
            else:
                self.config = config

        return self.config

    def python(self, arguments, **kwargs):
        include_console = kwargs.get('include_console', True)
        output_logfile = kwargs.get('output_logfile', os.path.join(self.appHome, 'log', 'code42.log'))
        write_stdout = kwargs.get('write_stdout', False)
        write_stderr = kwargs.get('write_stderr', False)

        if 'STDOUT' in os.environ and os.environ['STDOUT'] == 'true':
          write_stdout = True
          write_stderr = True
          output_logfile = None

        arguments.insert(0, self.PYTHONPATH)
        arguments.insert(1, '-u') # Unbuffered `python3` output stream (merge STDERR & logfile lines)

        if include_console:
            arguments.extend([  '-s', self.config['hostname'],
                                '-port', self.config['port'],
                                '-u', self.config['username'],
                                '-p', self.config['password']])
        if output_logfile:
            log_folder = os.path.dirname(output_logfile)
            if not os.path.exists(log_folder):
                os.makedirs(log_folder)

            arguments.extend([ '-log', output_logfile ])

        if 'PYTHONPATH' in os.environ:
            # Cross-Platform Python Path
            del os.environ['PYTHONPATH']
        if 'LD_LIBRARY_PATH' in os.environ:
            # Linux (non-Unix) Library Path
            del os.environ['LD_LIBRARY_PATH']
        if 'DYLD_LIBRARY_PATH' in os.environ:
            # Unix (non-Linux) Library Path
            del os.environ['DYLD_LIBRARY_PATH']

        process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # http://stackoverflow.com/a/9899753/296794
        def __logMessage(stream, type=0):
            while True:
                line = stream.readline()
                if not line:
                    break
                if type == 0:
                    if write_stdout:
                        sys.stdout.write(line)
                if type == 1:
                    if write_stderr:
                        sys.stderr.write(line)
                if output_logfile and line and ((not write_stdout and type == 0) or type != 0):
                    with open(output_logfile, 'a') as f:
                        f.write(line)


        stdout_thread = threading.Thread(target=__logMessage, args=(process.stdout, 0))
        stderr_thread = threading.Thread(target=__logMessage, args=(process.stderr, 1))

        stdout_thread.start()
        stderr_thread.start()

        stdout_thread.join()
        stderr_thread.join()

        # Make sure the `returncode` is set, and the script is finished.
        process.wait()
        if process.returncode != 0:
            raise Exception("Non-zero exit code when running external script.")

    def main(self):
        return

    def run(self):
        self.getConfig()

        self.main()
