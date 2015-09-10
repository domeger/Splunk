"""Django page classes for form view controllers"""
# NOTE: Using django.forms directly instead of splunkdj.setup.forms
from django import forms
from django.contrib import messages
import splunklib.client as client

class SetupForm(forms.Form):
    """Setup form for the Code42 App for Splunk settings"""

    console_hostname = forms.CharField(label="Console hostname")
    console_port = forms.IntegerField(label="Console port", initial=4285)

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

        # Verify that the credentials are valid by connecting to the Code42 server.
        credentials = [
            cleaned_data.get('console_hostname', None),
            cleaned_data.get('console_port', None),
            cleaned_data.get('console_username', None),
            console_password
        ]

        if None in credentials:
            # One of the credential fields didn't pass validation,
            # so don't even try connecting to the Code42 server.
            pass
        else:
            if not SetupForm._validate_server_credentials(credentials):
                raise forms.ValidationError('Invalid Code42 Server credentials.')

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
            'port': settings['console_port']
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
        passwords = [x for x in passwords_endpoint.list() if 'access' in x and 'app' in x['access'] \
                                                             and x['access']['app'] == 'code42']
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
        config_endpoint = client.Collection(service, 'code42/config/console')
        config_endpoint.post(**kwargs)

    @staticmethod
    def _validate_server_credentials(credentials):
        """Validate a configuration against a Code42 Server to test credentials"""
        hostname, port, username, password = credentials

        # TODO: Validate server credentials here.

        return True
