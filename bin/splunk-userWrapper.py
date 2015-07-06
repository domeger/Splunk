from _base import SplunkScript

import datetime
import json
import os
import sys

class UserWrapper(SplunkScript):
    def main(self):
        ##############################################################
        ## RUN THE USER ROLES EXPORTER & REFORMAT EVENTS FOR SPLUNK ##
        ##############################################################

        # Get current date/time
        now = datetime.datetime.now()
        timestamp = str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "-" + str(now.hour) + "-" + str(now.minute) + "-" + str(now.second)

        # Set up variables
        pyScript = os.path.join(self.appHome, 'utils', 'api', 'userRoles.py')
        tmpEventOutput = os.path.join(self.appHome, 'events', 'users-tmp')
        tmpEventFile = os.path.join(tmpEventOutput, timestamp + '-userRoles.txt')

        # Ensure the events tmp directory exists
        if not os.path.exists(tmpEventOutput):
            os.makedirs(tmpEventOutput)

        args = [ pyScript,
                 tmpEventFile
        ];
        self.python(args)

        # Reformat events for Splunk (JSON blobs per line)
        with open(tmpEventFile) as data_file:
            data = json.load(data_file)

        for role_dict in data:
            sys.stdout.write(json.dumps(role_dict) + "\n")

        os.remove(tmpEventFile)


script = UserWrapper()
script.run()
