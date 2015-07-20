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
        tmpEventFile = os.path.join(self.appHome, 'events', 'users.txt')

        args = [ pyScript,
                 tmpEventFile
        ];
        self.python(args)

        # Reformat events for Splunk (JSON blobs per line)
        with open(tmpEventFile, 'r') as data_file:
            data = json.load(data_file)

            for user_dict in data:
                sys.stdout.write(json.dumps(user_dict) + "\n")

        os.remove(tmpEventFile)


script = UserWrapper()
script.run()
