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

"""Django page classes for form view controllers"""
import sys
import os

# NOTE: Using django.forms directly instead of splunkdj.setup.forms
# pylint: disable=import-error
from django import forms
from django.contrib import messages
import splunklib.client as client

import c42api

class SetupForm(forms.Form):
    """Setup form for the Code42 App for Splunk settings"""

    console_hostname = forms.CharField(label="Console hostname")
    console_port = forms.CharField(label="Console port", initial='4285', required=False)
    console_verify_ssl = forms.BooleanField(label="Require SSL certificate validation", initial=True, required=False)

    script_devices = forms.CharField(label="Event Filter", required=False, help_text="""Filter imported objects to
                                         only items inside the defined list of devices or organizations.<br/>
                                         Device queries should be a comma separated list of deviceGUIDs, device names,
                                         or organization names (prefixed with "org:" each time). Blank value will
                                         import all objects.""")

    console_username = forms.CharField(label="Console username")
    console_password = forms.CharField(label="Console password", widget=forms.PasswordInput(), required=False)
    console_password_confirm = forms.CharField(label="Console password (again)", widget=forms.PasswordInput(),
                                               required=False)
    analytics_help_text = "We'll write some anonymous usage data to disk and you can send it to us later."
    console_collect_analytics = forms.BooleanField(label="Collect Analytics", initial=True, required=False,
                                                   help_text=analytics_help_text)

    # Non-form objects

    # HACK: See `clean()` function about why we need to store `service` as a
    #       class object on SetupForm.
    service = None

    @classmethod
    def load(cls, request):
        """Loads this form's persisted state, returning a new Form."""

        service = request.service

        # Get the configuration of this app from the encrypted credential store,
        # and from our custom config.conf file.
        credential = cls._get_credentials(service)
        console_config = cls._get_config(service, stanza='console')
        script_config = cls._get_config(service, stanza='script')

        settings = {}

        # Config settings always have a default embedded in the app, so we can
        # leave them as-is here.
        settings['console_hostname'] = console_config['hostname']
        settings['console_port'] = console_config['port']
        settings['console_collect_analytics'] = console_config['collect_analytics'] == 'true'

        settings['script_devices'] = script_config['devices']
        settings['console_verify_ssl'] = console_config['verify_ssl'] == 'true'

        # Credential settings may not exist, so we need the default to be explicitly
        # determined (usually empty strings) here.
        settings['console_username'] = credential['username'] if credential else ''

        obj = cls(settings)

        if credential:
            obj.fields['console_password'].help_text = "Leave blank to keep existing password."

        return obj

    def clean(self):
        """Perform validations that require multiple fields."""

        cleaned_data = super(SetupForm, self).clean()

        console_password = cleaned_data.get('console_password', None)
        console_password_confirm = cleaned_data.get('console_password_confirm', None)

        if console_password != console_password_confirm:
            raise forms.ValidationError('Passwords did not match.')

        if not console_password:
            # HACK: We don't have a way to get the service object in this instance
            #       because this is called automatically by splunkdj and skips it as
            #       an argument. We manually set this in `views.py`
            service = SetupForm.service

            credential = self._get_credentials(service)

            if not credential:
                raise forms.ValidationError('Username/password is required.')

            # The `save()` function is going to resave these credentials, so we need
            # to make sure it doesn't get saved as an empty password.
            self.cleaned_data['console_password'] = credential['clear_password']
            console_password = credential['clear_password']

        port = cleaned_data.get('console_port', None)
        if port and len(port) > 0:
            try:
                port = int(port)
            except ValueError:
                raise forms.ValidationError('Port must be a number or empty.')
        else:
            port = None

        hostname = cleaned_data.get('console_hostname', None)
        username = cleaned_data.get('console_username', None)
        verify_ssl = cleaned_data.get('console_verify_ssl', False)

        if not SetupForm._validate_server_credentials(hostname, username, console_password,
                                                      port=port, verify_ssl=verify_ssl):
            raise forms.ValidationError('Could not verify Code42 Server info or credentials.')

        return cleaned_data

    def save(self, request):
        """Saves this form's persisted state."""

        service = request.service
        settings = self.cleaned_data

        credential_settings = {
            'realm': '',
            'name': settings['console_username'],
            'password': settings['console_password']
        }
        config_settings = {
            'hostname': settings['console_hostname'],
            # We have to save empty value as a space, otherwise it turns into
            # the default value. Splunk trims strings automatically when reading
            # stanza items.
            'port': settings['console_port'] or ' ',
            'verify_ssl': 'true' if settings['console_verify_ssl'] else 'false',
            'collect_analytics': 'true' if settings['console_collect_analytics'] else 'false',
        }
        script_config_settings = {
            'devices': settings['script_devices'] or ' '
        }

        # Replace old password entity with new one.
        credential = self._get_credentials(service)
        if credential:
            credential.delete()

        self._set_credentials(service, **credential_settings)
        self._set_config(service, stanza='console', **config_settings)
        self._set_config(service, stanza='script', **script_config_settings)

        messages.success(request, 'Successfully saved settings.')

    @staticmethod
    def _get_credentials(service):
        """Get the correct, properly filtered Code42 Server credentials entity"""
        passwords_endpoint = client.Collection(service, 'storage/passwords')

        def _password_match(credential):
            """Determine whether a credential matches this app namespace"""
            try:
                return credential['access']['app'] == 'code42'
            except AttributeError:
                return False

        passwords = [x for x in passwords_endpoint.list() if _password_match(x)]
        credential = passwords[0] if len(passwords) > 0 else None

        return credential

    @staticmethod
    def _set_credentials(service, **kwargs):
        """Set new Code42 Server credentials entity"""
        passwords_endpoint = client.Collection(service, 'storage/passwords')
        passwords_endpoint.create(**kwargs)

    @staticmethod
    def _get_config(service, stanza='console'):
        """Get non-credential Code42 configuration settings entity"""
        config_endpoint = client.Collection(service, 'code42/config/%s' % stanza)
        configs = config_endpoint.list()

        return configs[0] if len(configs) > 0 else None

    @classmethod
    def _set_config(cls, service, stanza='console', **kwargs):
        """Set non-credential Code42 configuration settings entity"""
        config_endpoint = client.Collection(service, 'code42/config/%s' % stanza)
        config_endpoint.post(**kwargs)

    @staticmethod
    def _validate_server_credentials(hostname, username, password, port=None, verify_ssl=True):
        """Validate a configuration against a Code42 Server to test credentials"""

        server = c42api.Server(hostname, port=port, username=username, password=password, verify_ssl=verify_ssl)

        try:
            request = server.post('AuthToken')
            response = server.json_from_response(request)
        except (c42api.HTTPError, c42api.ConnectionError):
            return False

        return request.status_code == 200 and isinstance(response.get('data', None), list)
