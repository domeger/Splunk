# NOTE: Using django.forms directly instead of splunkdj.setup.forms
from django import forms
import os.path
import splunklib.client as client
import subprocess
import sys

class SetupForm(forms.Form):
    console_hostname = forms.CharField(label="Console hostname")
    console_port = forms.IntegerField(label="Console port")

    console_username = forms.CharField(label="Console username")
    console_password = forms.CharField(label="Console password", widget=forms.PasswordInput(), required=False)
    console_password_confirm = forms.CharField(label="Console password (again)", widget=forms.PasswordInput(), required=False)

    @classmethod
    def load(cls, request):
        """Loads this form's persisted state, returning a new Form."""

        service = request.service

        # Locate the storage/passwords entity that contains the Twitter
        # credentials, if available.
        #
        # It is only stored in storage/passwords because older versions of
        # this app put it there. If writing this app from scratch,
        # I'd probably put it in a conf file instead because it
        # is a lot easier to access.
        passwords_endpoint = client.Collection(service, 'storage/passwords')
        passwords = passwords_endpoint.list()
        first_password = passwords[0] if len(passwords) > 0 else None

        config_endpoint = client.Collection(service, 'code42/config')
        config = config_endpoint.list()

        settings = {}

        # Read credentials from the password entity.
        # NOTE: Reading from 'password' setting just gives a bunch of asterisks,
        #       so we need to read from the 'clear_password' setting instead.
        # NOTE: Reading from 'name' setting gives back a string in the form
        #       '<realm>:<username>', when we only want the username.
        #       So we need to read from the 'username' setting instead.
        settings['console_hostname'] = config[0]['hostname']
        settings['console_port'] = config[0]['port']

        settings['console_username'] = first_password['username'] if first_password else ''

        # Create a SetupForm with the settings
        return cls(settings)

    def clean(self):
        """Perform validations that require multiple fields."""

        cleaned_data = super(SetupForm, self).clean()

        console_password = cleaned_data.get('console_password', None)
        console_password_confirm = cleaned_data.get('console_password_confirm', None)

        if console_password != console_password_confirm:
            raise forms.ValidationError('Passwords did not match.')

        raise forms.ValidationError(str(self.__dict__))

        if not console_password:
            service = request.service

            passwords_endpoint = client.Collection(service, 'storage/passwords')
            passwords = passwords_endpoint.list()
            first_password = passwords[0] if len(passwords) > 0 else None

            cleaned_data.set('console_password', first_password['clear_password'])
            console_password = first_password['clear_password']

        # Verify that the credentials are valid by connecting to Twitter
        credentials = [
            cleaned_data.get('console_hostname', None),
            cleaned_data.get('console_port', None),
            cleaned_data.get('console_username', None),
            console_password
        ]

        if None in credentials:
            # One of the credential fields didn't pass validation,
            # so don't even try connecting to a Code42 server.
            pass
        else:
            if not SetupForm._validate_server_credentials(credentials):
                raise forms.ValidationError('Invalid Twitter credentials.')

        return cleaned_data

    def save(self, request):
        """Saves this form's persisted state."""

        service = request.service
        settings = self.cleaned_data

        first_password_settings = {
            'realm': '',
            'name': settings['console_username'],
            'password': settings['console_password']
        }

        # Replace old password entity with new one
        passwords_endpoint = client.Collection(service, 'storage/passwords')
        passwords = passwords_endpoint.list()
        if len(passwords) > 0:
            first_password = passwords[0]
            first_password.delete()
        first_password = passwords_endpoint.create(**first_password_settings)

    @staticmethod
    def _validate_server_credentials(credentials):
        hostname, port, username, password = credentials

        # TODO: Validate server credentials here.

        return True
