#!/usr/bin/env python3
#
# Copyright (c) 2015 - 2016 Code42 Software, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
