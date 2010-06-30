import os, sys
from mail.models import *
from django.core.management.base import BaseCommand, make_option

class Command(BaseCommand):
    """ Merges recipient accounts """
    
    def expand_victim_list(self, victims=[]):
        """ Grab everyone who's been merged into the victim list and merge them, too"""
        last_count = 0
        while True:
            expanded_set = Person.objects.filter(merged_into__in=victims)
            if last_count>=expanded_set.count():
                break
                
            else:
                for new_victim in expanded_set:
                    if not (new_victim.id in victims):
                        victims.append(new_victim.id)

            last_count = expanded_set.count()

        return victims
    
    def handle(self, *args, **options):
        target = Person.objects.get(id=args[0])
        target.merged_into = None
        target.save()
        
        victim_final = []
        victims = list(args[1:])
        victims = self.expand_victim_list(victims)
        name_list = []
        email_count = 0
        for victim in victims:
            p = Person.objects.get(id=victim)
            if len(p.name)>0:
                name_list.append(p.name.strip())
            else:
                name_list.append(p.alias.strip())

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
                
            sent_mail = Email.objects.filter(creator=p)
            for m in sent_mail:
                m.creator = target
                m.save()        
                email_count += 1        
            
            if len(target.alias.strip())==0 and len(p.alias.strip())>0:
                target.alias = p.alias
                target.save()
                
            p.merged_into = target
            p.save()
                
        print "Combined %s into the %s account, affecting %d emails" % (", ".join(name_list), target.name, email_count)
                
        
                
            