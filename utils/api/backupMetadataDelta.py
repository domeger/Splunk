#!/usr/bin/python

# File: backupMetadataDelta.py
# Author: Hank Brekke
# Last Modified: 06/24/2015
#
# Calculate a backup selection metadata delta between two dates
# for a list of computers.
#
# Usage: backupMetadataDelta.py [deviceName/deviceGuid] [date1] [date2]
#

import json

from dateutil.parser import parse
from _base import C42Script

class BackupMetadataDelta(C42Script):
	def description(self):
		return 'Calculate a backup selection metadata delta between two dates for a list of computers.'

	def setup_parser(self, parser):
		parser.add_argument('devices', help='Comma separated list of computer name or GUID, and/or organization name (prefixed with "org:")')
		parser.add_argument('date1', help='Date for the base during delta calculation (2015-06-24)')
		parser.add_argument('date2', help='Date for the opposing delta calculation (2015-06-24)')
		parser.add_argument('-o', '--output', dest='output', help='An optional output file as a CSV document')
		parser.add_argument('--no-color', default=True, dest='color', action='store_false', help='Disables colored output for delta (only applies when no output file specified)')

		super(BackupMetadataDelta, self).setup_parser(parser)

	def start(self):
		super(BackupMetadataDelta, self).start()

		self.args.devices = self.args.devices.split(',')
		self.args.date1 = parse(self.args.date1)
		self.args.date2 = parse(self.args.date2)

		if self.args.date1 > self.args.date2:
			# Always put the earlier date first when calculating delta.
			self.args.date1, self.args.date2 = self.args.date2, self.args.date1

	def outline(self):
		if self.args.output:
			self.log("Resolving Backup Selection Delta to " + self.args.output)
		else:
			self.log("Resolving Backup Selection Delta")
		self.log("> Devices:\t" + json.dumps(self.args.devices))
		self.log("> Base date:\t" + self.args.date1.isoformat())
		self.log("> Second date:\t" + self.args.date2.isoformat())

		super(BackupMetadataDelta, self).outline()

	def calculateDelta(self, deviceGUID):
		self.log('> Calculating delta for device %s.' % deviceGUID)

		params = {}
		params['webRestoreSessionId'] = webRestoreSessionId
		params['guid'] = srcGUID
		params['timestamp'] = 0
		params['regex'] = self.args.day
		payload = {}
		r = self.console.executeRequest("get", self.console.cp_api_archiveMetadata + "/%s" , params, payload)
		content = r.content.decode('UTF-8')
		binary = json.loads(content)

	def main(self):
		deviceGUIDs = self.search_devices(self.args.devices)

		for deviceGUID in deviceGUIDs:
			self.log('')
			self.calculateDelta(deviceGUID)

script = BackupMetadataDelta()
script.run()
