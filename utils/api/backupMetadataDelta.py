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

import os
import sys
import json
import datetime

from dateutil.parser import parse
from _base import C42Script, smart_open

class BackupMetadataDelta(C42Script):
    def description(self):
        return 'Calculate a backup selection metadata delta between two dates for a list of computers.'

    def setup_parser(self, parser):
        parser.add_argument('date1', help='Date for the base during delta calculation (2015-06-24)')
        parser.add_argument('date2', help='Date for the opposing delta calculation (2015-06-24)')
        parser.add_argument('-d', '--devices', dest='devices', help='Comma separated list of computer name or GUID, and/or organization name (prefixed with "org:")')
        parser.add_argument('-o', '--output', dest='output', help='An optional output file as a CSV document, "csv" or "json" for STDOUT formatting.')

        if os.name != 'nt':
            # Windows cannot print in color, so we hide the functionality.
            parser.add_argument('--no-color', default=True, dest='color', action='store_false', help='Disables colored output for delta (only applies when no output file specified)')

        parser.add_argument('-H', '--header', default=False, dest='header', action='store_true', help='Include header when outputting to a CSV document')
        parser.add_argument('--no-folders', default=True, dest='folders', action='store_false', help='Removes add/delete folder events from output results')

        super(BackupMetadataDelta, self).setup_parser(parser)

    def start(self):
        super(BackupMetadataDelta, self).start()

        if self.args.devices:
            self.args.devices = self.args.devices.split(',')

        self.args.date1 = parse(self.args.date1)
        self.args.date2 = parse(self.args.date2)

        if os.name == 'nt':
            # Windows cannot print in color, so we hide the functionality.
            self.args.color = False

        self.args.format = 'custom'
        if self.args.output:
            if self.args.output == 'csv':
                # CSV Output to STDOUT (and skip logging).
                self.args.format = 'csv'
                self.args.output = None
                self.logfile = os.devnull
            elif self.args.output.endswith('csv'):
                # CSV Output to file.
                self.args.format = 'csv'
            elif self.args.output == 'json':
                # JSON-per-line Output to STDOUT (and skip logging).
                self.args.format = 'json'
                self.args.output = None
                self.logfile = os.devnull
            else:
                self.args.color = False

        if self.args.date1 > self.args.date2:
            # Always put the earlier date first when calculating delta.
            self.args.date1, self.args.date2 = self.args.date2, self.args.date1

    def outline(self):
        if self.args.output:
            self.log("Resolving Backup Selection Delta to " + self.args.output)
        else:
            self.log("Resolving Backup Selection Delta")
        if self.args.devices:
            self.log("> Devices:\t" + json.dumps(self.args.devices))
        self.log("> Base date:\t" + self.args.date1.isoformat())
        self.log("> Second date:\t" + self.args.date2.isoformat())

        super(BackupMetadataDelta, self).outline()

    def __filterFileVersion(self, version):
        if not self.args.folders and version['fileType'] == 1:
            # We don't care about folder creation or deletions
            return False

        versionTimestamp = parse(version['versionTimestamp']).replace(tzinfo=None)
        return (versionTimestamp > self.args.date1 and versionTimestamp < self.args.date2)

    def __byteformat(self, num):
        for unit in ['bytes','KB','MB','GB','TB','PB','EB','ZB']:
            if num < 1024:
                return "%d %s" % (num, unit)
            num /= 1024.0
        return "%.1f %s" % (num, 'YB')

    def __str(self, obj):
        # http://code.activestate.com/recipes/466341-guaranteed-conversion-to-unicode-or-byte-string/
        return str(obj).encode('ascii', 'ignore').decode('unicode_escape')

    def __output(self, out, event):
        if self.args.format == 'csv':
            out.write("%s," % event['deviceGuid'])
            out.write("%s," % event['eventType'])

            out.write("%s," % event['files'][0]['MD5Hash'])
            out.write("%s," % event['files'][0]['fileEventType'])
            out.write("%s," % event['files'][0]['fileName'])
            out.write("%s," % event['files'][0]['fileType'])
            out.write("%s," % event['files'][0]['fullPath'])
            out.write("%s," % event['files'][0]['lastModified'])
            out.write("%s," % event['files'][0]['length'])

            out.write("%s" % event['timestamp'])

            out.write("\n")
        elif self.args.format == 'json':
            out.write("%s\n" % json.dumps(event))
        elif self.args.format == 'custom':
            COLOR = '\033[1m'
            END = '\033[0m'

            shape = '?'
            if event['eventType'] == 'BACKUP_FILE_ACTIVITY':
                shape = '*'
                COLOR = '\033[94m'
            elif event['eventType'] == 'BACKUP_FILE_DELETE':
                shape = '-'
                COLOR = '\033[91m'

            if self.args.color:
                out.write(COLOR)

            out.write(shape)
            if self.args.output:
                # Write the deviceGuid if we are writing our custom format to disk.
                out.write(" %s" % event['deviceGuid'])
            out.write(" %s" % event['files'][0]['fullPath'])
            if event['files'][0]['MD5Hash']:
                out.write(" (%s)" % event['files'][0]['MD5Hash'])

            date = datetime.datetime.fromtimestamp(event['timestamp'] / 1000.0)
            out.write(" %s" % str(date))

            if event['files'][0]['length'] > 0:
                out.write(" %s" % self.__byteformat(event['files'][0]['length']))

            if self.args.color:
                out.write(END)
            out.write("\n")

    def calculateDelta(self, deviceGUID):
        self.log('> Getting delta for device %s.' % deviceGUID)

        self.log('>> Getting archiveGuid for device.')
        # Getting archiveGuid for device.
        params = {}
        params['backupSourceGuid'] = deviceGUID
        r = self.console.executeRequest("get", self.console.cp_api_archive, params, {})
        content = r.content.decode('UTF-8')
        binary = json.loads(content)

        if not 'archives' in binary['data'] or len(binary['data']['archives']) == 0:
            raise Exception('Computer GUID does not have a backup archive.')

        archiveGUID = binary['data']['archives'][0]['archiveGuid']

        self.log('>> Getting Backup planUid from archiveGuid.')
        # Getting Backup planUid from archiveGuid.
        params = {}
        params['archiveGuid'] = archiveGUID
        r = self.console.executeRequest("get", self.console.cp_api_plan, params, {})
        content = r.content.decode('UTF-8')
        binary = json.loads(content)

        backupPlanUid = 0
        for backupPlan in binary['data']:
            if backupPlan['planType'] == 'BACKUP':
                backupPlanUid = backupPlan['planUid']

        if backupPlanUid == 0:
            raise Exception('Archive GUID does not have a backup plan.')

        self.log('>> Getting all file versions for Backup planUid.')
        # Getting all file versions for Backup planUid.
        params = {}
        params['idType'] = 'planUid'
        params['decryptPaths'] = 'true'
        params['includeAllVersions'] = 'true'
        r = self.console.executeRequest("get", self.console.cp_api_archiveMetadata + "/" + backupPlanUid, params, {})
        content = r.content.decode('UTF-8')
        binary = json.loads(content)

        self.log('>> Filtering file versions to specified range.')
        # Filtering file versions to specified range.
        delta = []
        lastFileVersion = None
        versions = sorted(binary['data'], key=lambda x: (x['path'], x['versionTimestamp']))
        for version in versions:
            if self.__filterFileVersion(version):
                event = {}
                event['deviceGuid'] = int(deviceGUID)
                event['timestamp'] = int(version['timestamp'])
                event['version'] = 1
                file = { 'fullPath': self.__str(version['path']),
                                    'fileName': self.__str(version['path'].split('/')[-1]),
                                    'length': int(version['sourceLength']),
                                    'MD5Hash': self.__str(version['sourceChecksum']),
                                    'lastModified': int(version['timestamp']),
                                    'fileType': int(version['fileType']) }

                if version['sourceChecksum'] == 'ffffffffffffffffffffffffffffffff':
                    # Checksum is none, file has been deleted.
                    event['eventType'] = 'BACKUP_FILE_DELETE'
                    file['fileEventType'] = 'delete'
                    file['MD5Hash'] = ''
                    file['length'] = 0
                else:
                    event['eventType'] = 'BACKUP_FILE_ACTIVITY'
                    file['fileEventType'] = 'activity'

                if version['fileType'] == 1:
                    # CrashPlan keeps some inacurate data about folders we want to remove.
                    file['MD5Hash'] = ''
                    file['length'] = 0

                event['files'] = [file]

                delta.append(event)
            lastFileVersion = version

        if len(delta) > 0:
            with smart_open(self.args.output) as out:
                for version in delta:
                    self.__output(out, version)
        else:
            self.log('NOTICE: Device %s does not have any backup activity between dates.' % deviceGUID)

    def main(self):
        deviceGUIDs = self.search_devices(self.args.devices)

        # Open the file & overwrite any previous content with empty (clean output).
        with smart_open(self.args.output, overwrite_file=True) as out:
            if self.args.format == 'csv' and self.args.header:
                out.write("deviceGuid,eventType,files_MD5Hash,files_fileEventType,files_fileName,files_fileType,files_fullPath,files_lastModified,files_length,timestamp\n")

        for deviceGUID in deviceGUIDs:
            self.log('')
            try:
                self.calculateDelta(deviceGUID)
            except Exception as e:
                sys.stderr.write("ERROR: %s\n" % str(e))

        self.log('')
        self.log('Finished calculating backup metadata delta.')

script = BackupMetadataDelta()
script.run()
