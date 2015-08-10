# File: splunk-userWrapper.py
# Author: Nick Wallin
#
# Calls external users script and prints user information
# to STDOUT for Splunk indexing.
#

from _base import SplunkScript

import json
import os
import sys

class UserWrapper(SplunkScript):
    def main(self):
        #########################################################
        ## RUN THE USERS EXPORTER & REFORMAT EVENTS FOR SPLUNK ##
        #########################################################

        # Set up variables
        pyScript = os.path.join(self.appHome, 'utils', 'users.py')
        eventsDir = os.path.join(self.appHome, 'events')
        tmpEventFile = os.path.join(eventsDir, 'users.txt')

        if not os.path.exists(eventsDir):
            os.makedirs(eventsDir)

        args = [ pyScript,
                 tmpEventFile
        ];
        self.python(args)

        with open(tmpEventFile, 'r') as data_file:
            # first line of file is '['
            data_file.readline()
            for line in data_file:
                if line.strip() not in [',',']']:
                    sys.stdout.write(json.dumps(json.loads(line)) + "\n")

        os.remove(tmpEventFile)


script = UserWrapper()
script.run()
