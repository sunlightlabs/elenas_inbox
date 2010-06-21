import os, sys
from mail.models import *
from django.core.management.base import BaseCommand, make_option

class Command(BaseCommand):
    """ Merges recipient accounts """
    def handle(self, *args, **options):
        target = Person.objects.get(id=args[0])
        victim_final = []
        victims = args[1:]
        name_list = []
        email_count = 0
        for victim in victims:
            p = Person.objects.get(id=victim)
            if len(p.name)>0:
                name_list.append(p.name)
            else:
                name_list.append(p.alias)

            to_mail = Email.objects.filter(to=p)
            for m in to_mail:
                m.to.remove(p)
                m.to.add(target)
                m.save()
                email_count += 1

            cc_mail = Email.objects.filter(cc=p)                
            for m in cc_mail:
                m.cc.remove(p)
                m.cc.add(target)
                m.save()
                email_count += 1                
                
            if len(target.alias.strip())==0 and len(p.alias.strip())>0:
                target.alias = p.alias()
                target.save()
                
            p.delete()
                
        print "Combined %s into the %s account, affecting %d emails" % (", ".join(name_list), target.name, email_count)
                
        
                
            