from _base import SplunkScript

import datetime
import os
import sys

class BackupDeltaWrapper(SplunkScript):
    def main(self):
        ##########################################################
        ## RUN THE BACKUP METADATA DELTA SCRIPT FOR EACH DEVICE ##
        ##########################################################

        # Get current date/time
        now = datetime.datetime.now()
        # Use 01-01-1970 unless a cursor file is found and parsed properly.
        lastRun = datetime.datetime.fromtimestamp(0)

        # Set up variables
        pyScript = os.path.join(self.appHome, 'utils', 'api', 'backupMetadataDelta.py')
        cursor = os.path.join(self.appHome, 'events', 'backupMetadataDelta-lastRun')

        if os.path.exists(cursor):
            # Read the ISO cursor of the lower range (upper range from last run).
            with open(cursor, 'r') as f:
                try:
                    isotime = f.read()
                    lastRun = datetime.datetime.strptime(isotime, "%Y-%m-%dT%H:%M:%S.%f")
                except:
                    sys.stderr.write("ERROR: Could not parse cursor timestamp file.\n")

        args = [ pyScript,
                 lastRun.isoformat(),
                 now.isoformat(),
                 '-o', 'json'
        ];
        if self.config['devices'] and len(self.config['devices']) > 0:
            args.extend(['-d', self.config['devices']])

        self.python(args, write_stdout=True)

        with open(cursor, 'w') as f:
            # Write the ISO cursor of the upper range (lower range for next run).
            f.write(now.isoformat())

script = BackupDeltaWrapper()
script.run()
