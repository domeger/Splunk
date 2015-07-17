# File: _base.py
# Author: Hank Brekke
# Last Modified: 06/24/2015
#
# Base class for performing common API actions, such as querying
# for devices or parsing arguments.
#

import sys
import abc
import argparse
import contextlib
import getpass
import json
import datetime

from c42SharedLibrary import c42Lib
import _c42_csv as csv

# http://stackoverflow.com/a/17603000/296794
@contextlib.contextmanager
def smart_open(filename=None, **kwargs):
	overwrite_file = kwargs.get('overwrite_file', False)

	if filename and filename != '-':
		style = 'a'
		if overwrite_file:
			style = 'w'
		fh = open(filename, style)
	else:
		fh = sys.stdout

	try:
		yield fh
	finally:
		if fh is not sys.stdout:
			fh.close()

class C42Script(object):
	logfile = None
	arg_parser = None
	args = {}
	console = None
	csv = None
	def __init__(self):
		description = self.description()
		self.arg_parser = argparse.ArgumentParser(description=description)
		self.console = c42Lib
		self.csv = csv

		self.setup_parser(self.arg_parser)

	# Public utilities
	def log(self, string, **kwargs):
		skip_time = kwargs.get('skip_time', False)

		with smart_open(self.logfile) as output:
			if self.logfile and not skip_time:
				date = datetime.datetime.now()
				output.write('%s %s\n' % (date.strftime("%Y-%m-%d %H:%M:%S"), string))
			else:
				output.write('%s\n' % string)

	# Metadata
	def description(self):
		return "Unknown script"

	def setup_parser(self, parser):
		parser.add_argument('-s', dest='hostname', default='https://spyder.code42.com', help='Code42 Console URL (without port)')
		parser.add_argument('-u', dest='username', default='admin', help='Code42 Console Username')
		parser.add_argument('-port', dest='port', default='4285', help='Code42 Console Port')
		parser.add_argument('-p', dest='password', default='', help='Code42 Console password (replaces prompt)')
		parser.add_argument('-log', dest='logfile', default=None, help='Logfile to print informational output messages (instead of STDOUT)')

	# Convenience methods
	def search_devices(self, queries, type='CrashPlan'):
		computers = []
		if not queries:
			# All devices (null queries)
			payload = {}
			params = {}
			r = self.console.executeRequest("get", self.console.cp_api_computer, params, payload)
			content = r.content.decode('UTF-8')
			binary = json.loads(content)

			if isinstance(binary, list):
				sys.stderr.write("ERROR: " + binary[0]['name'] + ": " + binary[0]['description'] + "\n")
			else:
				queryComputers = binary['data']['computers']
				if len(queryComputers) == 0:
					sys.stderr.write("ERROR: Computer " + query + " could not be found, or is not active.\n")

				for computer in queryComputers:
					if computer['service'] == type:
						srcGUID = computer['guid']
						if not srcGUID in computers:
							computers.append(srcGUID)
			return computers

		for query in queries:

			params = {}
			params['active'] = 'true'

			if query.startswith('org:'):
				orgQuery = query[4:]
				self.log(">> Querying organization information.")
				# Querying organization information.
				orgParams = {}
				orgParams['q'] = orgQuery
				orgPayload = {}
				r = self.console.executeRequest("get", self.console.cp_api_org, orgParams, orgPayload)
				content = r.content.decode('UTF-8')
				binary = json.loads(content)
				orgUid = binary['data']['orgs'][0]['orgUid']

				self.log(">> Querying all computers inside organization " + orgUid + ".")
				# Querying all computers inside organization.
				params['orgUid'] = orgUid
			else:
				self.log(">> Querying computers with name " + query + ".")
				# Querying all computers inside organization.
				params['q'] = query

			payload = {}
			r = self.console.executeRequest("get", self.console.cp_api_computer, params, payload)
			content = r.content.decode('UTF-8')
			binary = json.loads(content)

			if isinstance(binary, list):
				sys.stderr.write("ERROR: " + binary[0]['name'] + ": " + binary[0]['description'] + "\n")
			else:
				queryComputers = binary['data']['computers']
				if len(queryComputers) == 0:
					sys.stderr.write("ERROR: Computer " + query + " could not be found, or is not active.\n")

				for computer in queryComputers:
					if computer['service'] == type:
						srcGUID = computer['guid']
						if not srcGUID in computers:
							computers.append(srcGUID)

		self.log('>> Found ' + str(len(computers)) + ' devices matching queries.')
		return computers

	# Lifecycle
	def start(self):
		if not self.args:
			self.args = self.arg_parser.parse_args()

		if self.args.logfile and not self.logfile:
			self.logfile = self.args.logfile
			self.log('------------------------------------------', skip_time=True)

	def end(self):
		self.log('')

	def outline(self):
		self.log('> API URL:\t' + self.args.hostname + ':' + self.args.port)
		self.log('> Console User:\t' + self.args.username)

	def prepare(self):
		self.console.cp_host = self.args.hostname
		self.console.cp_port = self.args.port
		self.console.cp_username = self.args.username

		if len(self.args.password) > 0:
			self.console.cp_password = self.args.password
		else:
			self.args.password = getpass.getpass("Code42 Console Password [" + self.console.cp_username + "]: ")
			self.console.cp_password = self.args.password
			self.log('')

	@abc.abstractmethod
	def main(self):
		return

	def run(self):
		self.start()

		self.log('')
		self.outline()
		self.log('')

		self.prepare()

		self.main()

		self.end()
