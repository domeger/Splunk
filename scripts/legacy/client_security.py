#!/usr/bin/python
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

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '_include'))

from _base import C42Script

class ClientSecurity(C42Script):
    def description(self):
        return "Configures system & org properties to enable or disable the detection functionality in CrashPlan clients."

    def setup_parser(self, parser):
        parser.add_argument("orgName", help="Organization to change detection functionality.")
        parser.add_argument("enabled", nargs='?', default="get", help="Value to change detection functionality to (true|false). Exclude to retrieve current settings.")

        super(ClientSecurity, self).setup_parser(parser)

    def start(self):
        super(ClientSecurity, self).start()

        if self.args.enabled == "get":
            del self.args.enabled
        elif self.args.enabled.lower() == 'true' or self.args.enabled == '1':
            self.args.enabled = True
        else:
            self.args.enabled = False

    def outline(self):
        self.log.debug("Configuring organization detection functionality")
        self.log.debug("> Organization:\t%s" % self.args.orgName)
        if 'enabled' in self.args:
            self.log.debug("> Detection:\t%s" % self.args.enabled)
        super(ClientSecurity, self).outline()

    def __get_settings(self):
        self.log.debug(">> Checking if system property is enabled.")
        # Check if the system property needs to be enabled (prerequisite to org setting).
        payload = {"command": "prop.show cpc.securityModulesEnabled"}
        r = self.console.executeRequest("post", self.console.cp_api_cli, {}, payload)
        content = r.content.decode('UTF-8')
        binary = json.loads(content)
        values = binary['data'][0]['result']

        systemEnabled = (len(values) > 0 and values[0]['value'] == 'true')

        orgId = self.search_orgs(self.args.orgName)['orgId']

        self.log.debug(">> Checking if organization setting is enabled.")
        # Check if the system property needs to be enabled (prerequisite to org setting).
        params = { "keys": "org-securityTools-client-enable" }
        r = self.console.executeRequest("get", self.console.cp_api_orgSettings + "/" + str(orgId), params, {})
        content = r.content.decode('UTF-8')
        binary = json.loads(content)
        values = binary['data']

        orgEnabled = (len(values) > 0 and values['org-securityTools-client-enable']['value'] == 'true')

        return systemEnabled, orgEnabled, orgId

    def main(self):
        systemEnabled, orgEnabled, orgId = self.__get_settings()

        if not 'enabled' in self.args:
            self.log.debug("")
            self.log.debug("System property:\t%s" % systemEnabled)
            self.log.debug("Organization setting:\t%s" % orgEnabled)
            return

        if self.args.enabled and not systemEnabled:
            self.log.debug("> Enabling system property")

            payload = {'command': "prop.set cpc.securityModulesEnabled true save"}
            r = self.console.executeRequest("post", self.console.cp_api_cli, {}, payload)
            content = r.content.decode('UTF-8')
            binary = json.loads(content)
            values = binary['data'][0]['result']

        if self.args.enabled and not orgEnabled:
            self.log.debug("> Enabling organization setting")
            payload = {"packets":[
                { "key": "org-securityTools-client-enable",
                  "value": "true",
                  "locked": False }
            ]}
            r = self.console.executeRequest("put", self.console.cp_api_orgSettings + '/' + str(orgId), {}, payload)

            self.log.debug("")
            if r.status_code == 204:
                self.log.debug("Client Security Detection has been enabled for this organization.")
            else:
                self.log.error("Unknown error %d when configuring organization setting." % r.status)
                sys.exit(2)
        elif not self.args.enabled and orgEnabled:
            self.log.debug("> Disabling organization setting")
            payload = {"packets":[
                { "key": "org-securityTools-client-enable",
                  "value": "false",
                  "locked": False }
            ]}
            r = self.console.executeRequest("put", self.console.cp_api_orgSettings + '/' + str(orgId), {}, payload)
            self.log.debug("")
            if r.status_code == 204:
                self.log.debug("Client Security Detection has been disabled for this organization.")
            else:
                self.log.error("Unknown error %d when configuring organization setting." % r.status)
                sys.exit(2)
        else:
            self.log.debug("")
            self.log.debug("Organization has already been configured for this setting.")

if __name__ == "__main__":
    script = ClientSecurity()
    script.run()
