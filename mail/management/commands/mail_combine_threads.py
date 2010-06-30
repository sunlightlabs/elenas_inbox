import os, sys
from mail.models import *
from django.core.management.base import BaseCommand, make_option

class Command(BaseCommand):
    """ Merges recipient accounts """
    def handle(self, *args, **options):
        target = Thread.objects.get(id=args[0])
        victim_final = []
        victims = args[1:]
        name_list = []
        email_count = 0
        for victim in victims:
            t = Thread.objects.get(id=victim)
            name_list.append(t.name)

            target.star_count += t.star_count

            for m in Email.objects.filter(email_thread=t):
                m.email_thread = target
                m.save()
                email_count += 1
                                
            t.merged_into = target
            t.save()
            
        target.save()
        
        print "Combined %s into the %s account, affecting %d emails" % (", ".join(name_list), target.name, email_count)
                
        
                
