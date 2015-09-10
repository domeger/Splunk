"""Django URL dispatcher"""

from django.conf.urls import patterns, url

# pylint: disable=invalid-name

URLS = [
    # NOTE: The framework always expects the default view to be called 'home'.
    #       And it expects the default view to be a framework view.
    #       In this case the default view is actually a non-framework view,
    #       so an explicit redirect needs to be inserted to make the
    #       framework happy.
    url(r'^home/$', 'code42.views.home', name='home'),
    url(r'^setup/$', 'code42.views.setup', name='setup')
]

urlpatterns = patterns('', *URLS)
