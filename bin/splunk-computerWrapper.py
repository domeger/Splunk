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
        tmpEventFile = os.path.join(self.appHome, 'events', 'computers.txt')

        args = [ pyScript,
                 tmpEventFile
        ];
        self.python(args)

        # Reformat events for Splunk (JSON blobs per line)
        with open(tmpEventFile, 'r') as data_file:
            data = json.load(data_file)

            for computer_dict in data:
                sys.stdout.write(json.dumps(computer_dict) + "\n")

        os.remove(tmpEventFile)


script = ComputerWrapper()
script.run()
