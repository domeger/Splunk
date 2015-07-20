#!/usr/bin/env python3

# File: computers.py
# Author: Nick Wallin
# Last Modified: 07/13/2015
#
# Usage: computers.py [-s HOSTNAME] [-u USERNAME] [-port PORT] [-p PASSWORD] output
#

import datetime
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '_include'))
from _base import C42Script

class C42Computers(C42Script):
    def description(self):
        return "Export Code42 computer information."

    def setup_parser(self, parser):
        parser.add_argument("output", help="An output file with data in JSON format.")
        super(C42Computers, self).setup_parser(parser)

    def outline(self):
        self.log("Exporting computer information to " + self.args.output)
        super(C42Computers, self).outline()

    def main(self):
        timestamp = datetime.datetime.now().isoformat()
        computers = self.console.getAllDevices()
        output_file = self.args.output
        with open(output_file, "w") as f:
            json_array = []
            for computer in computers:
                try:
                    computer['timestamp'] = timestamp
                    computer['schema_version'] = 1
                    json_array.append(computer)
                except KeyError:
                    continue
            json.dump(json_array, f)

script = C42Computers()
script.run()
