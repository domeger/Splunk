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

# http://docs.splunk.com/Documentation/Splunk/6.0/AdvancedDev/SetupExampleCustom

import os
import json

import splunk.admin as admin
import splunk.entity as en

class ConfigApp(admin.MConfigHandler):
  def setup(self):
    if self.requestedAction == admin.ACTION_EDIT:
      args = ['hostname', 'port', 'verify_ssl']
      for arg in args:
        self.supportedArgs.addOptArg(arg)

  def writeInputs(self):
    inputsFile = os.path.join(os.environ['SPLUNK_HOME'], 'etc', 'apps', 'code42', 'default', 'inputs.json')
    entities = []
    with open(inputsFile) as data:
      inputConfs = json.load(data)

      for value in inputConfs:
        protocol = value['protocol']
        path = os.path.join(*value['path'])
        self.writeConf('inputs', "%s://%s" % (protocol, path), value['settings'])

        if not protocol in entities:
          entities.append(protocol)

    for entity in entities:
      entityPath = "/data/inputs/%s" % entity
      en.refreshEntities(entityPath, sessionKey=self.getSessionKey())

  def handleList(self, confInfo):
    confDict = self.readConf("c42config")
    if None != confDict:
      for stanza, settings in confDict.items():
        for key, val in settings.items():
          if val in [None, '']:
            val = ''
          confInfo[stanza].append(key, val)

  def itemDefault(self, name, default = ''):
    if self.callerArgs.data[name][0] in [None, '']:
        self.callerArgs.data[name][0] = default

  def handleEdit(self, confInfo):
    name = self.callerArgs.id
    args = self.callerArgs

    if name == 'console':
      # /code42/config/console [console stanza]

      self.itemDefault('hostname', '')
      self.itemDefault('port', '4285')
      self.itemDefault('verify_ssl', 'true')

    self.writeConf('c42config', name, self.callerArgs.data)
    self.writeInputs()

# initialize the handler
admin.init(ConfigApp, admin.CONTEXT_NONE)
