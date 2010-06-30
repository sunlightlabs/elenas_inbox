from django.core.management.base import NoArgsCommand, BaseCommand
from mail.models import *
from django.core.management import call_command

class Command(NoArgsCommand):
    
    def _buf_is_already_merged(self, buf):
        unmerged_count = 0        
        for b in buf:
            print '###', b, b.merged_into
            if b.merged_into is None:
                unmerged_count += 1
                
        return (unmerged_count==1)
    
    def handle_noargs(self, **options):
        buf = []
        last_name = None
        for p in Person.objects.all().order_by('name_hash', 'id'):

            # time to clear the buffer?
            if last_name is not None and last_name!=p.name_hash:

                # do nothing on empty buf
                if len(buf)>1:     
                    
                    # make sure we haven't already merged these guys
                    found_names = {}
                    for x in buf:
                        found_names[x.name] = True
                    print found_names
                    
                    if (len(found_names.keys())>1) and (not self._buf_is_already_merged(buf)):
                    
                        print last_name
                        for i in range(0, len(buf)):
                            print "  %d. %s" % (i, str(buf[i]))
                        print "  %d. No merge" % len(buf)
                        choice_num = raw_input('Merge into: ')

                        if choice_num.upper().strip()=='R':
                            new_name = raw_input('New name: ')
                            new_name = new_name.strip()
                            for p in buf:
                                p.name = new_name
                                p.save()
                        
                            call_command('mail_combine_people', *(map(lambda x: x.id, buf))) # it doesn't matter who we merge into since they all have the same name
                    
                        else:

                            if int(choice_num)<(len(buf)):
                                print "got %d" % int(choice_num)
                                choice = buf[int(choice_num)]

                                other_ids = [choice.id]
                                for x in buf:
                                    if x.id!=choice.id:
                                        other_ids.append(x.id)

                                print "merging %s into %s" % (map(lambda x: int(x), other_ids), choice.name)

                                call_command('mail_combine_people', *other_ids)                    
                
                buf = [p]                
                
            else:
                buf.append(p)    
            
            last_name = p.name_hash
