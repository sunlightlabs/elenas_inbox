from django.core.management.base import NoArgsCommand, BaseCommand
import re, os, hashlib

class Command(BaseCommand):
    help = "Extract Kagan email data into individual files."    

    def emit(self, filename, count, buf):        
        out = open('parsed/source/%s/%d.txt' % (hashlib.md5(filename).hexdigest(), count), 'w')
        out.write("".join(buf))
        out.close()
        

    def handle(self, *args, **options):

        files = []
        for p in args:
            if os.path.exists(p):
                files.append(p)
        
        re_record_start = re.compile(r'.?\s*RECORD\sTYPE:')
        re_garbage = re.compile(r'(^.?\s*http://[\]\[\|\(\)lI1]72\.|/servlet/getEmaiIArchive|\x0c|ARMS\sEmail\sSystem\s{3,})')
        re_redaction = re.compile(r'withdr', re.I)
        re_withdrawal = re.compile(r'redac', re.I)
        re_page_end = re.compile(r'\x0c')
        
        count = 0
        for filename in files:
            
            dir = 'parsed/source/%s' % hashlib.md5(filename).hexdigest()
            if not os.path.exists(dir):
                os.mkdir(dir)
            
            buf = []
            collecting = False
            f = open(filename, 'r')
            while True:
                line = f.readline()
                if not line:
                    break
                
                # skip over redaction marker pages
                if (re_redaction.search(line) is not None) and (re_withdrawal.search(line) is not None):
                    if collecting:
                        self.emit(filename, count, buf)
                        count += 1
                        collecting = False
                        
                    while True:
                        line = f.readline()
                        if (re_page_end.search(line) is not None) or (re_record_start.match(line) is not None):
                            break
                
                
                
                # new record? clear out the buffer (if there is a buffer)
                if re_record_start.match(line) is not None:
                    if collecting and len(buf)>0:
                        self.emit(filename, count, buf)
                        count += 1
                    collecting = True
                    buf = []
        
        
        
                # add to buffer... if not garbage
                if re_garbage.search(line) is None:
                    buf.append(line)
        
                                
            f.close()
        
        print "Extracted %d mail objects" % count

            
                
