from django.core.management.base import NoArgsCommand
import re
from mail.models import *

class Command(NoArgsCommand):
    help = "Import Kagan email data."

    def _make_boxes(self):
        Box.objects.all().delete()
        BOXES = {
            '1': 'OPD',
            '2': 'OPD',
            '3': 'OPD',
            '4': 'OPD',
            '5': 'OPD',
            '6': 'OPD',
            '7': 'OPD',
            '8': 'OPD',
            '10': 'WHO',
            '11': 'WHO',
            '12': 'WHO',
            '13': 'WHO',
            '14': 'WHO',
            '15': 'WHO',
            '16': 'CEA',
            '16': 'DEFAULT'
        }
        
        for (number, name) in BOXES.items():
            b = Box()
            b.name = name
            b.number = int(number)
            b.save()
        

    def handle_noargs(self, **options):
        self._make_boxes()
        # FILES = ('../pdf/KAGAN-ARMS SENT Boxes 01-10.txt', '../pdf/KAGAN-ARMS SENT Boxes 11-16.txt')
        FILES = ('../pdf/combined.txt',)
        
        re_record_start = re.compile(r'.?\s*RECORD\sTYPE:')
        re_record_end = re.compile(r'(^.?\s*http://[\]\[\|\(\)lI1]72\.|/servlet/getEmaiIArchive|\x0c)')
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
                

                if collecting and ((blank_count>=3) or (re_record_end.search(line) is not None)):
                    if len(buf)>0:
                        Email.objects.parse_text(filename, buf)
                    buf = []
                    blank_count = 0
                    collecting = False
                                
            f.close()
        
        print "Found %d mail objects" % Email.objects.count
        print "No matches on %d names" % Email.objects.failure
            
                
