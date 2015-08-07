#!/usr/bin/env python3

# File: backupMetadataDelta.py
# Author: Hank Brekke
#
# Calculate a backup selection metadata delta between two dates
# for a list of computers.
#
# Usage: backupMetadataDelta.py [date1] [date2]
#

import os
import sys
import json
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '_include'))

from dateutil.parser import parse
from _base import C42Script, smart_open

class BackupMetadataDelta(C42Script):
    def description(self):
        return 'Calculate a backup selection metadata delta between two dates for a list of computers.'

    def setup_parser(self, parser):
        parser.add_argument('date1', help='Date for the base during delta calculation (2015-06-24)')
        parser.add_argument('date2', help='Date for the opposing delta calculation (2015-06-24)')
        parser.add_argument('-d', '--device', dest='device', help='A computer name or GUID for delta calculation.')
        parser.add_argument('-o', '--output', dest='output', help='An optional output file as a CSV document, "csv" or "json" for STDOUT formatting.')

        if os.name != 'nt':
            # Windows cannot print in color, so we hide the functionality.
            parser.add_argument('--no-color', default=True, dest='color', action='store_false', help='Disables colored output for delta (only applies when no output file specified)')

        parser.add_argument('-H', '--header', default=False, dest='header', action='store_true', help='Include header when outputting to a CSV document')
        parser.add_argument('--no-folders', default=True, dest='folders', action='store_false', help='Removes add/delete folder events from output results')

        super(BackupMetadataDelta, self).setup_parser(parser)

    def start(self):
        super(BackupMetadataDelta, self).start()

        self.args.devices = None
        if self.args.device:
            self.args.devices = self.args.device.split(',')

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
            elif self.args.output.endswith('json'):
                self.args.format = 'json'
            else:
                self.args.color = False

        if self.args.logfile:
            self.logfile = self.args.logfile

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
            # Skip folder creation or deletions with `--no-folder` argument.
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
        if self.args.format == 'json':
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
        else:
            raise Exception("Unexpected output format '%s'" % self.args.format)

    def calculateDelta(self, deviceGUID):
        self.log('> Getting delta for device %s.' % deviceGUID)

        self.log('>> Getting dataKeyToken for device.')
        # Getting dataKeyToken for device.
        payload = {
            'computerGuid': deviceGUID
        }
        r = self.console.executeRequest("post", self.console.cp_api_dataKeyToken, {}, payload)
        dataKeyTokenResponse = json.loads(r.content.decode("UTF-8"))
        dataKeyToken = dataKeyTokenResponse['data']['dataKeyToken'] if 'data' in dataKeyTokenResponse else None

        with self.storage_server(device_guid=deviceGUID) as server:
            self.log('>> Getting all file versions for device.')
            # Getting all file versions for device.
            params = {}
            params['idType'] = 'guid'
            params['decryptPaths'] = 'true'
            params['dataKeyToken'] = dataKeyToken
            '''
            We want to `includeAllVersions` for full history, but v1 archive (CrashPlan) support
            is not available until server is v5.0, so we'll update this script when the minimum version
            for these scripts reaches v5.0 and later.
            '''
            # params['includeAllVersions'] = 'true'
            r = server.executeRequest("get", server.cp_api_archiveMetadata + "/" + deviceGUID, params, {})
            content = r.content.decode('UTF-8')
            binary = json.loads(content)

        if not 'data' in binary:
            raise Exception("[%s] - %s" % (binary[0]['name'], binary[0]['description']))

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
                event['schema_version'] = 1
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
            return delta
        else:
            self.log('NOTICE: Device %s does not have any backup activity between dates.' % deviceGUID)
            return []

    def main(self):
        deviceGUIDs = self.search_devices(self.args.devices)

        if len(deviceGUIDs) > 1:
            sys.stdout.write("\n")
            sys.stderr.write("**************************************************************************************\n")
            sys.stderr.write("*** THIS SCRIPT DOES NOT PERFORM AT SCALE, AND CAN ONLY BE RUN FOR A SINGLE DEVICE ***\n")
            sys.stderr.write("*** PLEASE ADD `-d deviceGuid` TO THE CLI ARGUMENTS & TRY AGAIN                    ***\n")
            sys.stderr.write("**************************************************************************************\n")
            sys.stdout.write("\n")
            sys.exit(1)

        # Open the file & overwrite any previous content with empty (clean output).
        if self.args.output and os.path.exists(self.args.output):
            os.remove(self.args.output)

        keyset = self.csv.KeySet()

        for deviceGUID in deviceGUIDs:
            self.log('')
            try:
                delta = self.calculateDelta(deviceGUID)
                if len(delta) > 0:
                    with smart_open(self.args.output) as out:
                        if self.args.format == 'csv':
                            if keyset.count() == 0:
                                # Build the keyset for the first device & version, reuse it beyond that.
                                for key, value in delta[0].items():
                                    json_key = self.csv.create_key(key, value)
                                    keyset.add_key(json_key)
                                if self.args.header:
                                    key_header = []
                                    for top_level_key in keyset.all_keys():
                                        key_header = self.csv.flattened_keys(top_level_key, key_header)
                                    out.write(",".join(key_header) + "\n")
                            for version in delta:
                                values = []
                                array_length = self.csv.dict_contains_array(version)
                                if array_length > -1:
                                    for i in range(0, array_length):
                                        values = []
                                        for top_level_key in keyset.all_keys():
                                            values = values + self.csv.dict_into_values(version, top_level_key, i)
                                        csvstring = self.csv.create_csv_string(values)
                                        out.write(csvstring + "\n")

                                else:
                                    for top_level_key in keyset.all_keys():
                                        values = values + self.csv.dict_into_values(version, top_level_key)
                                    csvstring = self.csv.create_csv_string(values)
                                    out.write(csvstring + "\n")
                        else:
                            for version in delta:
                                self.__output(out, version)


            except Exception as e:
                sys.stderr.write("ERROR: %s\n" % str(e))

        self.log('')
        self.log('Finished calculating backup metadata delta.')

script = BackupMetadataDelta()
script.run()
