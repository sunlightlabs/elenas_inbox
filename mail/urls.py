from django.views.generic.simple import direct_to_template, redirect_to
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^/?$', 'mail.views.index', name='index'),
    url(r'^sent/', 'mail.views.sent', name='sent'),

    url(r'^thread/(?P<thread_id>[0-9]+)/', 'mail.views.thread_by_id', name='thread_by_id'),
    url(r'^thread/(?P<thread_name>[\w\-]+)/', 'mail.views.thread_by_name', name='thread_by_name'),

    url(r'^contact/(?P<contact_id>[0-9]+)/', 'mail.views.contact_by_id', name='contact_by_id'),
    url(r'^contact/(?P<contact_name>[\w\-]+)/', 'mail.views.contact_by_name', name='contact_by_name'),
    
    url(r'^contacts/', 'mail.views.contacts_index', name='contacts_index'),    
    url(r'^search/', 'mail.views.search', name='search'),
    url(r'^starred/all/', 'mail.views.starred_all', name='starred_all'),
    url(r'^starred/', 'mail.views.starred', name='starred'),
    url(r'^star/ajax/(?P<thread_id>[0-9]+)/(?P<action>(add|remove))/', 'mail.views.star_record_ajax', name='star_record_ajax'),        
)