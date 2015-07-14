#!/usr/bin/env python3

# File: users.py
# Author: Nick Wallin
# Last Modified: 07/13/2015
#
# Usage: users.py [-s HOSTNAME] [-u USERNAME] [-port PORT] [-p PASSWORD] output
#

import datetime
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '_include'))
from _base import C42Script

class C42Users(C42Script):
    def __getActiveUsersPaged(self,pgNum,params = {}):
        params['pgNum'] = str(pgNum)
        params['pgSize'] = str(self.console.MAX_PAGE_NUM)
        params['active'] = True

        payload = {}

        r = self.console.executeRequest("get", self.console.cp_api_user, params, payload)

        content = r.content.decode('UTF-8')
        binary = json.loads(content)

        users = binary['data']['users']
        return users


    def __getUsers(self):
        currentPage = 1
        keepLooping = True
        fullList = []
        while keepLooping:
            pagedList = self.__getActiveUsersPaged(currentPage)
            if pagedList:
                fullList.extend(pagedList)
            else:
                keepLooping = False
            currentPage += 1
        return fullList

    
    def description(self):
        return "Export Code42 user information."

    def setup_parser(self, parser):
        parser.add_argument("output", help="An output file with data in JSON format.")
        super(C42Users, self).setup_parser(parser)

    def outline(self):
        self.log("Exporting User information to " + self.args.output)
        super(C42Users, self).outline()

    def __roles_for_user(self, user_id):
        params = {}
        payload = {}
        r = self.console.executeRequest("get", self.console.cp_api_userRole + "/" + str(user_id), params, payload)
        content = r.content.decode("UTF-8")
        binary = json.loads(content)
        roles = binary['data']
        return roles

    def main(self):
        users = self.__getUsers()
        output_file = self.args.output
        with open(output_file, "w") as f:
            timestamp = datetime.datetime.now().isoformat()
            json_array = []
            for user in users:
                try:
                    user_id = user["userId"]
                    user_uid = user["userUid"]
                    roles_json_string = self.__roles_for_user(user_id)
                    user["roles"] = roles_json_string
                    user["timestamp"] = timestamp
                    json_array.append(user)
                except KeyError:
                    continue
            json.dump(json_array, f)


script = C42Users()
script.run()
