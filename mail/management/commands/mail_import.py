from django.core.management.base import NoArgsCommand
import os
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

        Email.objects.all().delete()

        count = 0
        success = 0
        for filename in os.listdir('parsed/source'):
            f = open('parsed/source/%s' % filename, 'r')
            lines = f.readlines()
            f.close()
            source_id = filename[:filename.index('.')]
            
            if Email.objects.parse_text(source_id, lines):
                success += 1
            
            count += 1
            
        
        print "Imported %d of %s mail objects" % (success, count)
            
                
