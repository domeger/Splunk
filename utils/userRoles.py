#! /usr/bin/python

# File: userRoles.py
# Author: Nick Wallin
# Last Modified: 06/25/2015
#
# Usage: userRoles.py [-s HOSTNAME] [-u USERNAME] [-port PORT] [-p PASSWORD] output
#

import sys
import os
import datetime
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '_include'))

from _base import C42Script

class UserRoles(C42Script):
    def description(self):
        return "Export Code42 user role information."

    def setup_parser(self, parser):
        parser.add_argument("output", help="An output file with data in JSON format.")
        super(UserRoles, self).setup_parser(parser)

    def outline(self):
        self.log("Exporting User Role information to " + self.args.output)
        super(UserRoles, self).outline()

    def __roles_for_user(self, user_id):
        params = {}
        payload = {}
        r = self.console.executeRequest("get", self.console.cp_api_userRole + "/" + str(user_id), params, payload)
        content = r.content.decode("UTF-8")
        binary = json.loads(content)
        roles = binary['data']
        return roles

    def main(self):
        users = self.console.getAllUsers()
        output_file = self.args.output
        with open(output_file, "w") as f:
            timestamp = datetime.datetime.now().isoformat()
            json_array = []
            for user in users:
                try:
                    user_uid = user["userUid"]
                    user_id = user["userId"]
                    roles_json_string = self.__roles_for_user(user_id)
                    json_dict = {}
                    json_dict["userUid"] = user_uid
                    json_dict["timestamp"] = timestamp
                    json_dict["roles"] = roles_json_string
                    json_array.append(json_dict)
                except KeyError:
                    continue
            json.dump(json_array, f)


script = UserRoles()
script.run()
