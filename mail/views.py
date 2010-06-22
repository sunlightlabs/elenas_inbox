from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.paginator import Paginator
from urllib import unquote
from haystack.query import SearchQuerySet
from mail.models import *
from django.db.models import Q
import re

RESULTS_PER_PAGE = 50
    
def _search_tokens(request):
    s = request.GET.get('q', None)
    if s is None:
        return []
        
    # protection!
    re_sanitize = re.compile(r'[^\w\d\s\'"\,\.\?\$]', re.I)
    s = re_sanitize.sub('', s)
    
    tokens = []
    re_quotes = re.compile(r'\"([^\"]+)\"')
    for m in re_quotes.findall(s):
        tokens.append(m.replace('"','').strip())        
        s = s.replace('"%s"' % m, '')
    for t in s.split(' '):
        tokens.append(t.strip())

    while '' in tokens:
        tokens.remove('')
        
    return tokens
    
def _highlight(text, tokens):
    regexes = []
    for t in tokens:
        regexes.append(re.compile(r'(%s)' % t, re.I))
    for r in regexes:
        text = r.sub('<span class="highlight">\\1</span>', text)
    return text


def _annotate_threads(request, threads):
    read_cookie = unquote(request.COOKIES.get('kagan_read','')).replace(',,', ',')
    if len(read_cookie)>0:
        if read_cookie[0]==',':
            read_cookie = read_cookie[1:]
        if read_cookie[-1]==',':
            read_cookie = read_cookie[:-1]

    try:
        read_ids = map(lambda x: (x!='') and int(x) or 0, read_cookie.split(','))
    except:
        read_ids = []

    threads_obj = []
    for thread in threads:
        threads_obj.append({'read': (thread.id in read_ids), 'obj': thread})
    return threads_obj
    
def _annotate_emails(emails, search=[]):
    r = []
    for email in emails:
        email.text = _highlight(email.text, search)
        r.append({ 'to_html': email.to_html(), 'cc_html': email.cc_html(), 'obj': email })
    return r

def index(request, search=[], threads=None):
    
    if threads is None:
        threads_count = Thread.objects.all().count()
        threads = Thread.objects.all().order_by('-date')        
    else:
        threads_count = threads.count()
        if type(threads) is SearchQuerySet:
            threads = map(lambda x: x.object, threads)            
        
    p = Paginator(threads, RESULTS_PER_PAGE)
    
    page_num = 1
    try:
        page_num = int(request.GET.get('page', 1))
    except:
        pass
    page = p.page(page_num)

    threads = []
    for thread in page.object_list:
        thread.name = _highlight(thread.name, search)
        threads.append(thread)
        
    threads = _annotate_threads(request,threads)
    
    return render_to_response('index.html', {'range': "<strong>%d</strong> - <strong>%d</strong> of <strong>%d</strong>" % (page.start_index(), page.end_index(), threads_count), 'num_pages': p.num_pages , 'next': page_num<p.num_pages and min(p.num_pages,page_num+1) or False, 'prev': page_num>1 and max(1, page_num-1) or False, 'first': '1', 'last': p.num_pages, 'current_page': page_num, 'threads': threads, 'search': " ".join(search)}, context_instance=RequestContext(request))

def contact(request, contact_id):
    try:
        person = Person.objects.get(id=contact_id)
    except Thread.DoesNotExist, e:
        return HttpResponseRedirect(reverse('mail.views.index'))
    
    threads = []
    emails = Email.objects.filter(Q(to=person)|Q(cc=person))
    for e in emails:
        threads.append(e.email_thread.id)
    threads = Thread.objects.filter(id__in=threads).order_by('-date')


    return index(request, threads=threads)
    

def thread(request, thread_id):
    try:
        thread = Thread.objects.get(id=thread_id)
    except Thread.DoesNotExist, e:
        return HttpResponseRedirect(reverse('mail.views.index'))
    
    search = _search_tokens(request)
    
    emails = _annotate_emails(Email.objects.filter(email_thread=thread).order_by('creation_date_time'), search)    
    
    return render_to_response('thread.html', {'thread': thread, 'emails': emails }, context_instance=RequestContext(request))
    
def search(request):
    tokens = _search_tokens(request)
    if len(tokens) is None:
        return HttpResponseRedirect(reverse('mail.views.index'))
    
    sqs = SearchQuerySet().models(Thread)
    for t in tokens:
        sqs = sqs.filter_or(text_and_recipients=t)
    sqs = sqs.order_by('-date')

    return index(request, search=tokens, threads=sqs)

