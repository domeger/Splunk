#!/usr/bin/env python3

# File: computers.py
# Author: Nick Wallin
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

    def end(self):
        self.log("Finished exporting computer events.")

    def main(self):
        timestamp = datetime.datetime.now().isoformat()
        output_file = self.args.output
        with open(output_file, "w") as f:
            f.write("[\n")
            current_page = 1
            paged_list = True
            first_item = True
            while paged_list:
                paged_list = self.console.getDevices(current_page)
                for computer in paged_list:
                    computer['timestamp'] = timestamp
                    computer['schema_version'] = 1
                    if not first_item:
                        f.write(",\n")
                    else:
                        first_item = False
                    json.dump(computer, f)
                    f.write("\n")
                current_page += 1
            f.write("]")

script = C42Computers()
script.run()
