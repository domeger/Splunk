# File: _base.py
# Author: Hank Brekke
#
# Base class for performing common API actions, such as querying
# for devices or parsing arguments.
#

import sys
import abc
import argparse
import contextlib
import getpass
import json
import urllib
import logging

from c42SharedLibrary import c42Lib

@contextlib.contextmanager
def smart_open(filename=None, **kwargs):
    overwrite_file = kwargs.get('overwrite_file', False)
    std_stream = kwargs.get('std_stream', sys.stdout)

    if filename and filename != '-':
        style = 'a'
        if overwrite_file:
            style = 'w'
        fh = open(filename, style)
    else:
        fh = std_stream

    try:
        yield fh
    finally:
        if fh is not std_stream:
            fh.close()


class C42Script(object):
    arg_parser = None
    args = {}
    console = None
    log = None

    def __init__(self):
        description = self.description()
        self.arg_parser = argparse.ArgumentParser(description=description)
        self.console = c42Lib
        self.setup_parser(self.arg_parser)
        self._suppress_logs = False

    @property
    def suppress_logs(self):
        return self._suppress_logs

    @suppress_logs.setter
    def suppress_logs(self, value):
        self._suppress_logs = value
        self.log = self.create_logger()

    # Metadata
    def description(self):
        return "Unknown script"

    def create_logger(self):
        logger_name = type(self).__name__
        log = logging.getLogger(logger_name)
        try:
            logfile = self.args.logfile
        except AttributeError:
            return

        formatter = logging.Formatter('%(message)s')
        if logfile:
            handler = logging.FileHandler(logfile)
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s:%(funcName)s %(message)s')
        elif not self.suppress_logs:
            handler = logging.StreamHandler(sys.stdout)
        else:
            handler = logging.StreamHandler(sys.stderr)

        handler.setFormatter(formatter)
        log.handlers = [handler]
        log.setLevel(logging.DEBUG if (logfile or not self.suppress_logs) else logging.WARN)
        log.propagate = False
        return log

    def setup_parser(self, parser):
        parser.add_argument('-s', dest='hostname', default='https://spyder.code42.com', help='Code42 Console URL (without port)')
        parser.add_argument('-u', dest='username', default='admin', help='Code42 Console Username')
        parser.add_argument('-port', dest='port', default=4285, type=int, help='Code42 Console Port')
        parser.add_argument('--no-verify', dest='verify_ssl', action='store_false', default=True, help='Disable SSL certificate verification when making HTTPS requests.')
        parser.add_argument('-p', dest='password', default='', help='Code42 Console password (replaces prompt)')
        parser.add_argument('-log', dest='logfile', default=None, help=argparse.SUPPRESS)

    # Convenience methods
    def search_orgs(self, orgName):
        self.log.debug(">> Querying organization information.")

        orgParams = {}
        orgParams['q'] = orgName
        orgPayload = {}
        r = self.console.executeRequest("get", self.console.cp_api_org, orgParams, orgPayload)
        content = r.content.decode('UTF-8')
        binary = json.loads(content)
        orgs = binary['data']['orgs']

        if len(orgs) == 0:
            self.log.error("No organizations found with the name '%s'.", orgName)
            sys.exit(2)

        return orgs[0]

    def search_devices(self, queries, type='CrashPlan'):
        computers = []
        if not queries:
            # All devices (null queries)
            payload = {}
            params = {}
            r = self.console.executeRequest("get", self.console.cp_api_computer, params, payload)
            content = r.content.decode('UTF-8')
            binary = json.loads(content)

            if isinstance(binary, list):
                self.log.error(binary[0]['name'] + ": " + binary[0]['description'])
            else:
                queryComputers = binary['data']['computers']
                if len(queryComputers) == 0:
                    self.log.warn("No active computers could be found in this Code42 system.")

                for computer in queryComputers:
                    if computer['service'] == type:
                        srcGUID = computer['guid']
                        if not srcGUID in computers:
                            computers.append(srcGUID)
            return computers

        for query in queries:
            params = {}
            params['active'] = 'true'

            if query.startswith('org:'):
                orgQuery = query[4:]
                # Querying organization information
                orgUid = self.search_orgs(orgQuery)['orgUid']

                self.log.debug(">> Querying all computers inside organization " + orgUid + ".")
                # Querying all computers inside organization.
                params['orgUid'] = orgUid
            else:
                self.log.debug(">> Querying computers with name " + query + ".")
                # Querying all computers inside organization.
                params['q'] = query

            payload = {}
            r = self.console.executeRequest("get", self.console.cp_api_computer, params, payload)
            content = r.content.decode('UTF-8')
            binary = json.loads(content)

            if isinstance(binary, list):
                self.log.error(binary[0]['name'] + ": " + binary[0]['description'])
            else:
                queryComputers = binary['data']['computers']
                if len(queryComputers) == 0:
                    self.log.error("Computer " + query + " could not be found, or is not active.")

                for computer in queryComputers:
                    if computer['service'] == type:
                        srcGUID = computer['guid']
                        if not srcGUID in computers:
                            computers.append(srcGUID)

        self.log.debug('>> Found ' + str(len(computers)) + ' devices matching queries.')
        return computers

    # Cache some information we can reuse throughout several `storage_server` calls.
    __all_destinations = None
    __all_servers = None
    @contextlib.contextmanager
    def storage_server(self, plan_uid=None, device_guid=None):
        authority_host = self.console.cp_host
        authority_port = self.console.cp_port

        if not device_guid and not plan_uid:
            raise Exception("You need a device_guid or plan_uid to authorize a storage server.")

        if device_guid:
            self.log.debug('>>> Get backup planUid from deviceGuid %s.' % device_guid)
            # Get backup planUid from deviceGuid.
            params = {
                'sourceComputerGuid': device_guid,
                'planTypes': 'BACKUP'
            }
            r = self.console.executeRequest("get", self.console.cp_api_plan, params, {})
            backup_plans_response = json.loads(r.content.decode("UTF-8"))
            backup_plans = backup_plans_response['data'] if 'data' in backup_plans_response else None
            if backup_plans and len(backup_plans) > 0:
                plan_uid = backup_plans[0]['planUid']

        if not plan_uid:
            raise Exception("There are no backup planUid's for this device. Backup likely has not started, or deviceGuid is invalid.")

        self.log.debug('>>> Get storage locations for planUid %s.' % plan_uid)
        # Get Storage locations for planUid.
        r = self.console.executeRequest("get", "%s/%s" % (self.console.cp_api_storage, plan_uid), {}, {})
        storage_destinations_response = json.loads(r.content.decode("UTF-8"))
        storage_destinations = storage_destinations_response['data'] if 'data' in storage_destinations_response else None

        if len(storage_destinations) == 0:
            raise Exception("There is no storage location for this device archive. Backup has likely not started.")

        if not self.__all_destinations:
            self.log.debug('>>> Get information about all storage destinations.')
            # Get information about all storage destinations.
            r = self.console.executeRequest("get", self.console.cp_api_destination, {}, {})
            all_destinations_response = json.loads(r.content.decode("UTF-8"))
            self.__all_destinations = all_destinations_response['data']['destinations'] if 'data' in all_destinations_response else None
        all_destinations = self.__all_destinations

        if not self.__all_servers:
            self.log.debug('>>> Get information about all storage servers.')
            # Get information about all storage servers.
            r = self.console.executeRequest("get", self.console.cp_api_server, {}, {})
            all_servers_response = json.loads(r.content.decode("UTF-8"))
            self.__all_servers = all_servers_response['data']['servers'] if 'data' in all_servers_response else None
        all_servers = self.__all_servers

        # TODO: We need to ping each server and choose the fastest one, rather than going down the list serially.
        for destination_guid, server in storage_destinations.items():
            destination = [x for x in all_destinations if x['guid'] == destination_guid][0]
            server_full = ([x for x in all_servers if x['websiteHost'] == server['url']][:1] or [None])[0]
            if server_full and server_full['type'] == 'SERVER':
                # No special authorization is required for MASTER servers.

                self.log.debug(">>> Private MASTER server authorization complete.")
                # Private MASTER server authorization complete.
                break
            else:
                # Storage is on a separate server, and we need to authorize against it.

                self.log.debug(">>> Checking connection URL accuracy for storage server.")
                # Checking connection URL accuracy for storage server.
                payload = {
                    "planUid": str(plan_uid),
                    "destinationGuid": destination_guid
                }
                r = c42Lib.executeRequest("post", c42Lib.cp_api_storageAuthToken, {}, payload)
                storage_singleUseToken_response = json.loads(r.content.decode("UTF-8"))
                if not 'data' in storage_singleUseToken_response:
                    raise Exception("Failed to get storage auth token from destinationGuid %s - [%s]: %s." % (destination_guid, storage_singleUseToken_response[0]['name'], storage_singleUseToken_response[0]['description']))

                storage_url = urllib.parse.urlparse(storage_singleUseToken_response['data']['serverUrl'])
                storage_host = "%s://%s" % (storage_url.scheme, storage_url.hostname)
                storage_port = str(storage_url.port) if storage_url.port else ''
                storage_singleUseToken = storage_singleUseToken_response['data']['loginToken']

                self.console.cp_host = storage_host
                self.console.cp_port = storage_port

                if destination['type'] == 'PROVIDER':
                    self.log.debug(">>> Authorizing for a PROVIDER server (Code42 Hybrid Cloud, etc. not owned by the master server).")
                    # Authorizing for a PROVIDER server (Code42 Hybrid Cloud, etc. not owned by the master server).
                    c42Lib.cp_authorization = "LOGIN_TOKEN %s" % storage_singleUseToken
                    r = c42Lib.executeRequest("post", c42Lib.cp_api_authToken, {}, {})
                    storage_authToken_response = json.loads(r.content.decode("UTF-8"))

                    c42Lib.cp_authorization = "TOKEN %s-%s" % (storage_authToken_response['data'][0], storage_authToken_response['data'][1])
                    self.log.debug(">>> Shared PROVIDER server authorization complete.")
                    # Shared PROVIDER server authorization complete.
                else:
                    self.log.debug(">>> Private STORAGE server authorization complete.")
                    # Private STORAGE server authorization complete.

                break

        try:
            yield self.console
        finally:
            self.console.cp_host = authority_host
            self.console.cp_port = authority_port


    # Lifecycle
    def start(self):
        if not self.args:
            self.args = self.arg_parser.parse_args()

        self.log = self.create_logger()

        if len(self.args.hostname) > 0 and not self.args.hostname.startswith('http'):
          # Try and figure out a protocol for this hostname

          if self.args.port in [443, 4285, 7285]:
            self.args.hostname = "https://%s" % self.args.hostname
          else:
            self.args.hostname = "http://%s" % self.args.hostname

    def end(self):
        self.log.debug('')

    def outline(self):
        if ((self.args.hostname.startswith('https:') and self.args.port == 443) or
            (self.args.hostname.startswith('http:') and self.args.port == 80) or
            self.args.port <= 0):
            # Don't display the port if it's the default port for that protocol (443 or 80)
            self.log.debug('> API URL:\t' + self.args.hostname)
        else:
            self.log.debug('> API URL:\t' + self.args.hostname + ':' + str(self.args.port))
        self.log.debug('> Console User:\t' + self.args.username)

    def prepare(self):
        self.console.cp_host = self.args.hostname
        # Use port `0` for excluding port in HTTP requests (for some port-forwarding environments).
        self.console.cp_port = str(self.args.port) if self.args.port > 0 else ""
        self.console.cp_username = self.args.username
        self.console.cp_verify_ssl = self.args.verify_ssl

        if len(self.args.password) > 0:
            self.console.cp_password = self.args.password
        else:
            self.args.password = getpass.getpass("Code42 Console Password [" + self.console.cp_username + "]: ")
            self.console.cp_password = self.args.password
            self.log.debug('')

    @abc.abstractmethod
    def main(self):
        return

    def run(self):
        self.start()

        self.log.debug('')
        self.outline()
        self.log.debug('')

        self.prepare()

        self.main()

        self.end()
