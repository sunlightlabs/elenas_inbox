from django.core.management.base import NoArgsCommand
from django.db.models import Max, Min
import os
from mail import timedelta_to_days
from mail.models import *
from datetime import timedelta

class Command(NoArgsCommand):
    help = " Builds email threads "

    def handle_noargs(self, **options):

        THREAD_INACTIVITY_THRESHOLD = 30.0

        emails = Email.objects.filter(email_thread=None).order_by('subject_hash', 'creation_date_time')
        current_subject = None
        chain = []
        total = 0
        for e in emails:
            
            # check for an existing thread to which this mail can be added
            found_a_home = False
            potential_threads = Thread.objects.filter(name=e.subject_hash).order_by('-date')
            for pt in potential_threads:
                email_stats = Email.objects.filter(email_thread=pt).aggregate(Max('creation_date_time'), Min('creation_date_time'))
                if email_stats['creation_date_time__min'] is None:
                    time_before_first = 0
                else:
                    time_before_first = timedelta_to_days(email_stats['creation_date_time__min'] - e.creation_date_time)
                if email_stats['creation_date_time__max'] is None:
                    time_after_last = 0
                else:
                    time_after_last = timedelta_to_days(e.creation_date_time - email_stats['creation_date_time__max'])
                if (time_before_first<THREAD_INACTIVITY_THRESHOLD) and (time_after_last<THREAD_INACTIVITY_THRESHOLD):
                    e.email_thread = pt
                    e.save()
                    pt.save()
                    print "Added email '%s' to existing thread '%s'" % (e.subject, pt.name)
                    found_a_home = True
                    break
                
            # otherwise, proceed as normal
            if not found_a_home:
            
                if current_subject is None:
                    current_subject = e.subject_hash

                days_since_last = 0
                if len(chain)>0:
                    days_since_last = timedelta_to_days(e.creation_date_time - chain[-1].creation_date_time)

                # transitioning subject hashes?
                if (e.subject_hash!=current_subject) or (days_since_last>THREAD_INACTIVITY_THRESHOLD):
                    # make thread
                    t = Thread()
                    t.name = current_subject
                    t.date = chain[-1].creation_date_time # should be most recent
                    t.count = len(chain)
                    t.save()
            
                    # assign emails to thread
                    for c in chain:
                        c.email_thread = t
                        c.save()
            
                    print "Created chain '%s' with %d emails" % (current_subject, len(chain))
                    total += 1
            
                    # start new chain
                    chain = [e]
                    current_subject = e.subject_hash

                else:
                    chain.append(e)
        
        print "Created %d chains." % total