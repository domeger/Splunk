# http://docs.splunk.com/Documentation/Splunk/6.0/AdvancedDev/SetupExampleCustom

import os
import json

import splunk.admin as admin
import splunk.entity as en

class ConfigApp(admin.MConfigHandler):
  def setup(self):
    if self.requestedAction == admin.ACTION_EDIT:
      args = ['hostname', 'port', 'devices']
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

    self.writeInputs()

    if name == 'console':
      # /code42/config/console [console stanza]

      self.itemDefault('hostname', '')
      self.itemDefault('port', '4285')

      hostname = self.callerArgs.data['hostname'][0]
      if len(hostname) > 0 and not hostname.startswith('http'):
        # Try and figure out a protocol for this hostname

        if int(self.callerArgs.data['port'][0]) in [443, 4285, 7285]:
          self.callerArgs.data['hostname'][0] = "https://%s" % hostname
        else:
          self.callerArgs.data['hostname'][0] = "http://%s" % hostname
    elif name == 'script':
      # /code42/config/script [script stanza]

      self.itemDefault('devices', '')

    self.writeConf('c42config', name, self.callerArgs.data)

# initialize the handler
admin.init(ConfigApp, admin.CONTEXT_NONE)
