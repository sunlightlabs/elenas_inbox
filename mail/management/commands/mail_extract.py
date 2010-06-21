from django.core.management.base import NoArgsCommand
import re

class Command(NoArgsCommand):
    help = "Extract Kagan email data into individual files."    

    def handle_noargs(self, **options):

        FILES = ('../pdf/combined.txt',)
        
        re_record_start = re.compile(r'.?\s*RECORD\sTYPE:')
        re_record_end = re.compile(r'(^.?\s*http://[\]\[\|\(\)lI1]72\.|/servlet/getEmaiIArchive|\x0c)')
        count = 0
        for filename in FILES:
            buf = []
            blank_count = 0
            collecting = False
            f = open(filename, 'r')
            while True:
                line = f.readline()
                if not line:
                    break
                            
                if re_record_start.match(line) is not None:
                    collecting = True
        
                if collecting:
                    buf.append(line)
        
                line_stripped = line.strip()
                if len(line_stripped)==0:
                    blank_count += 1
                else:
                    blank_count = 0
                

                if collecting and (re_record_end.search(line) is not None):
                    if len(buf)>0:
                        out = open('parsed/source/%d.txt' % count, 'w')
                        out.write("".join(buf))
                        out.close()
                        count += 1

                    buf = []
                    blank_count = 0
                    collecting = False
                                
            f.close()
        
        print "Extracted %d mail objects" % count

            
                
