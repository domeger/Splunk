# File: splunk-computerWrapper.py
# Author: Nick Wallin
#
# Calls external computers script and prints user information
# to STDOUT for Splunk indexing.
#

from _base import SplunkScript

import json
import os
import sys

class ComputerWrapper(SplunkScript):
    def main(self):
        #############################################################
        ## RUN THE COMPUTERS EXPORTER & REFORMAT EVENTS FOR SPLUNK ##
        #############################################################

        # Set up variables
        pyScript = os.path.join(self.appHome, 'utils', 'computers.py')
        eventsDir = os.path.join(self.appHome, 'events')
        tmpEventFile = os.path.join(eventsDir, 'computers.txt')

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
                    try:
                        sys.stdout.write(json.dumps(json.loads(line)) + "\n")
                    except ValueError:
                        pass

        os.remove(tmpEventFile)


script = ComputerWrapper()
script.run()
