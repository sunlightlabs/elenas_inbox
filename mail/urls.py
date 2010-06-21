from django.views.generic.simple import direct_to_template, redirect_to
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^/?$', 'mail.views.index', name='index'),
    url(r'^thread/(?P<thread_id>[0-9]+)/', 'mail.views.thread', name='thread'),
)