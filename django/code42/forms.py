"""Django page classes for form view controllers"""
import base64
import requests
import json

# NOTE: Using django.forms directly instead of splunkdj.setup.forms
# pylint: disable=import-error
from django import forms
from django.contrib import messages
import splunklib.client as client

class SetupForm(forms.Form):
    """Setup form for the Code42 App for Splunk settings"""

    console_hostname = forms.CharField(label="Console hostname")
    console_port = forms.CharField(label="Console port", initial='4285', required=False)
    console_verify_ssl = forms.BooleanField(label="Require SSL certificate validation", initial=True, required=False)

    console_username = forms.CharField(label="Console username")
    console_password = forms.CharField(label="Console password", widget=forms.PasswordInput(), required=False)
    console_password_confirm = forms.CharField(label="Console password (again)", widget=forms.PasswordInput(),
                                               required=False)

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
        config = cls._get_config(service)

        settings = {}

        # Config settings always have a default embedded in the app, so we can
        # leave them as-is here.
        settings['console_hostname'] = config['hostname']
        settings['console_port'] = config['port']
        settings['console_verify_ssl'] = config['verify_ssl'] == 'true'

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
            'verify_ssl': 'true' if settings['console_verify_ssl'] else 'false'
        }

        # Replace old password entity with new one.
        credential = self._get_credentials(service)
        if credential:
            credential.delete()

        self._set_credentials(service, **credential_settings)
        self._set_config(service, **config_settings)

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
    def _get_config(service):
        """Get non-credential Code42 configuration settings entity"""
        config_endpoint = client.Collection(service, 'code42/config')
        configs = config_endpoint.list()

        return configs[0] if len(configs) > 0 else None

    @classmethod
    def _set_config(cls, service, **kwargs):
        """Set non-credential Code42 configuration settings entity"""
        config_endpoint = client.Collection(service, 'code42/config/console')
        config_endpoint.post(**kwargs)

    @staticmethod
    def _validate_server_credentials(hostname, username, password, port=None, verify_ssl=True):
        """Validate a configuration against a Code42 Server to test credentials"""

        token = base64.b64encode("%s:%s" % (username, password)).decode('UTF-8')

        header = {}
        header["Authorization"] = "Basic %s" % token
        header["Content-Type"] = "application/json"

        url = hostname.rstrip('/')
        if not hostname.startswith('http'):
            # Try and figure out a protocol for this hostname

            if not port:
                # Assume port-forwarding environments use HTTPS.
                url = "https://%s" % hostname
            if port in [443, 4285, 7285]:
                url = "https://%s" % hostname
            else:
                url = "http://%s" % hostname

        if port:
            url = "%s:%d" % (url, port)

        url = "%s/api/AuthToken" % url

        try:
            request = requests.post(url, headers=header, verify=verify_ssl)
        except requests.RequestException:
            return False

        response = json.loads(request.content)

        return request.status_code == 200 and isinstance(response.get('data', None), list)
