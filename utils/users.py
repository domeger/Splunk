#!/usr/bin/env python3
#
# Copyright (c) 2015 - 2016 Code42 Software, Inc.
#
# This source file is under the license available at
# https://github.com/code42/Splunk/blob/master/LICENSE.md

import datetime
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '_include'))
from _base import C42Script

class C42Users(C42Script):
    def description(self):
        return "Export Code42 user information."


    def setup_parser(self, parser):
        parser.add_argument("output", help="An output file with data in JSON format.")
        super(C42Users, self).setup_parser(parser)


    def outline(self):
        self.log("Exporting User information to " + self.args.output)
        super(C42Users, self).outline()

    def end(self):
        self.log("Finished exporting user events.")

    def main(self):
        timestamp = datetime.datetime.now().isoformat()
        output_file = self.args.output
        with open(output_file, "w") as f:
            f.write("[\n")
            params = {}
            params['active'] = 'true'
            params['incRoles'] = 'true'
            current_page = 1
            paged_list = True
            first_item = True
            while paged_list:
                paged_list = self.console.getUsersPaged(current_page, params)
                for user in paged_list:
                    user['timestamp'] = timestamp
                    user['schema_version'] = 1
                    if not first_item:
                        f.write(",\n")
                    else:
                        first_item = False
                    json.dump(user, f)
                    f.write("\n")
                current_page += 1
            f.write("]")


script = C42Users()
script.run()
