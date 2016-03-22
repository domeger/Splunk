# Copyright (c) 2015 - 2016 Code42 Software, Inc.
#
# This source file is under the license available at
# https://github.com/code42/Splunk/blob/master/LICENSE.md

"""Django URL dispatcher"""

# pylint: disable=import-error
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
