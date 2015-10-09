"""Django view controller hook"""

# pylint: disable=import-error
from .forms import SetupForm
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from splunkdj.decorators.render import render_to
from splunkdj.setup import create_setup_view_context

@login_required
def home(_):
    """Redirect to the default view, which is an XML dashboard (non-Django)"""
    return redirect('/en-us/app/code42/crashplan')

@render_to('code42:setup.html')
@login_required
def setup(request):
    """Render the setup page, and process data when it's validating/saving new content"""
    service = request.service
    SetupForm.service = service
    result = create_setup_view_context(
        request,
        SetupForm,
        reverse('code42:setup'))

    return result
