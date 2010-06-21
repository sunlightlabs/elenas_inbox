from django.core.management.base import NoArgsCommand
import os
from mail.models import *
from datetime import timedelta

class Command(NoArgsCommand):
    help = " Builds email threads "

    def handle_noargs(self, **options):

        def _timedelta_to_days(td):
            return td.days + (td.seconds / (60*60*24.0))

        Thread.objects.all().delete()

        blacklist = ['', 'attached', 'receipt notification'] # not yet used

        emails = Email.objects.all().order_by('subject_hash', 'creation_date_time')
        current_subject = None
        chain = []
        for e in emails:
            if current_subject is None:
                current_subject = e.subject_hash

            # transitioning subject hashes?
            if e.subject_hash!=current_subject:
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
            
                # stats
                if len(chain)>1:
                    cmax = None
                    cmin = None
                    cavg = timedelta(0, 0)
                    for i in range(0, len(chain)-1):
                        diff = chain[i+1].creation_date_time - chain[i].creation_date_time
                        if (cmax is None) or (diff > cmax):
                            cmax = diff
                        if (cmin is None) or (diff < cmin):
                            cmin = diff
                        cavg += diff
                
                    t.avg_interval = str(_timedelta_to_days(cavg) / (1.0 * (len(chain)-1)))
                    t.max_interval = str(_timedelta_to_days(cmax))
                    t.min_interval = str(_timedelta_to_days(cmin))
                    t.save()
            
                print "Created chain '%s' with %d emails" % (current_subject, len(chain))
            
                # start new chain
                chain = [e]
                current_subject = e.subject_hash

            else:
                chain.append(e)