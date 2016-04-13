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

"""
REST API handler for saving a custom conf file for internal Code42 App
settings, such as hostname and post

http://docs.splunk.com/Documentation/Splunk/6.0/AdvancedDev/SetupExampleCustom
"""

import os
import json

import splunk.admin as admin
import splunk.entity as en


class ConfigApp(admin.MConfigHandler):
    """
    Subclass of splunk's config handler. Used for handling changes.
    """
    def setup(self):
        """
        Setup function called by Splunk.
        """
        if self.requestedAction == admin.ACTION_EDIT:
            args = ['hostname', 'port', 'verify_ssl', 'devices', 'collect_analytics']
            for arg in args:
                self.supportedArgs.addOptArg(arg)

    def write_inputs(self):
        """
        Writes out values to a json file.
        """
        inputs_file = os.path.join(os.environ['SPLUNK_HOME'], 'etc', 'apps', 'code42', 'default', 'inputs.json')
        entities = []
        with open(inputs_file) as data:
            input_confs = json.load(data)

            for value in input_confs:
                protocol = value['protocol']
                path = os.path.join(*value['path'])
                self.writeConf('inputs', "%s://%s" % (protocol, path), value['settings'])

                if protocol not in entities:
                    entities.append(protocol)

        for entity in entities:
            entity_path = "/data/inputs/%s" % entity
            en.refreshEntities(entity_path, sessionKey=self.getSessionKey())

    def item_default(self, name, default=''):
        if self.callerArgs.data[name][0] in [None, '']:
            self.callerArgs.data[name][0] = default

    # pylint: disable=invalid-name
    def handleList(self, conf_info):
        """
        Used for creating a custom setup screen.

        http://wiki.splunk.com/Create_setup_screen_using_a_custom_endpoint
        """
        conf_dict = self.readConf("c42config")
        if conf_dict:
            for stanza, settings in conf_dict.items():
                for key, val in settings.items():
                    if val in [None, '']:
                        val = ''
                    conf_info[stanza].append(key, val)

    # pylint: disable=invalid-name
    def handleEdit(self, _):
        """
        Used for creating a custom setup screen.

        http://wiki.splunk.com/Create_setup_screen_using_a_custom_endpoint
        """
        name = self.callerArgs.id
        args = self.callerArgs

        self.write_inputs()

        if name == 'console':
            # /code42/config/console [console stanza]

            self.item_default('hostname', '')
            self.item_default('port', '4285')
            self.item_default('verify_ssl', 'true')
            self.item_default('collect_analytics', 'true')

        elif name == 'script':
            # /code42/config/script [script stanza]

            self.item_default('devices', '')

        self.writeConf('c42config', name, self.callerArgs.data)


# initialize the handler
if __name__ == '__main__':
    admin.init(ConfigApp, admin.CONTEXT_NONE)
