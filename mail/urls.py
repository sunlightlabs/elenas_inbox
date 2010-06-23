from django.views.generic.simple import direct_to_template, redirect_to
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^/?$', 'mail.views.index', name='index'),
    url(r'^thread/(?P<thread_id>[0-9]+)/', 'mail.views.thread', name='thread'),
    url(r'^contact/(?P<contact_id>[0-9]+)/', 'mail.views.contact', name='contact'),
    url(r'^contacts/', 'mail.views.contacts_index', name='contacts_index'),    
    url(r'^search/', 'mail.views.search', name='search'),
    url(r'^starred/', 'mail.views.starred', name='starred'),
    url(r'^starred/all/', 'mail.views.starred_all', name='starred_all'),
    url(r'^star/ajax/(?P<thread_id>[0-9]+)/(?P<action>(add|remove))/', 'mail.views.star_record_ajax', name='star_record_ajax'),        
)