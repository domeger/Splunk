import os
import sys
import subprocess
import glob
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
			possiblePaths = glob.glob("C:\Python3*")

			for possiblePath in possiblePaths:
				possiblePython = "%s\python.exe" % possiblePath
				if os.path.exists(possiblePython):
					PYTHONPATH = possiblePython
					break

		if not PYTHONPATH:
			sys.stderr.write("Python3 is not installed. Reverting to (potentially unstable) default Python.\n")

			# We can't use `which("python")` because it will pick up on Splunk's embedded Python.
			PYTHONPATH = "/usr/bin/python"

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

	def getConfig(self):
		if not self.config:
			sessionKey = self.getSessionKey()

			try:
				# list all credentials
				passwordEntities = entity.getEntities(['admin', 'passwords'], namespace='code42', owner='nobody', sessionKey=sessionKey)
				configConsoleEntities = entity.getEntities(['code42', 'config', 'console'], namespace='code42', owner='nobody', sessionKey=sessionKey)
				configScriptEntities = entity.getEntities(['code42', 'config', 'script'], namespace='code42', owner='nobody', sessionKey=sessionKey)
			except Exception as e:
				raise Exception("Could not get code42 credentials from splunk. Error: %s" % (str(e)))

			config = {}

			for i, c in passwordEntities.items():
				config['username'] = c['username']
				config['password'] = c['clear_password']

			for i, c in configConsoleEntities.items():
				config['hostname'] = c['hostname']
				config['port'] = c['port']

			for i, c in configScriptEntities.items():
				if c['devices'] != None and len(c['devices']) > 0:
					config['devices'] = c['devices']
				else:
					config['devices'] = None

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
			arguments.extend([	'-s', self.config['hostname'],
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
				if output_logfile and line:
					with open(output_logfile, 'a') as f:
						f.write(line)


		stdout_thread = threading.Thread(target=__logMessage, args=(process.stdout, 0))
		stderr_thread = threading.Thread(target=__logMessage, args=(process.stderr, 1))

		stdout_thread.start()
		stderr_thread.start()

		stdout_thread.join()
		stderr_thread.join()

	def main(self):
		return

	def run(self):
		self.getConfig()

		self.main()
