from django.core.management.base import BaseCommand
import os
from mail.models import *

class Command(BaseCommand):
    help = "Import Kagan email data."

    def handle(self, *args, **options):

        path = args[0]
        if not os.path.exists(path):
            print "Directory '%s' is not a valid path" % path
            return

        if not path.endswith('/'):
            path += '/'

        count = 0
        success = 0
        for filename in os.listdir(path):
            f = open('%s%s' % (path, filename), 'r')
            lines = f.readlines()
            f.close()
            source_id = filename[:filename.index('.')]
            
            if Email.objects.parse_text(source_id, path.split('/')[-2], lines):
                success += 1
            
            count += 1
            
        
        print "Imported %d of %s mail objects" % (success, count)
            
                
