from django.db import models
from settings import *
from dateutil import parser
import re


class Box(models.Model):
    """ An email 'box' (as defined by the ARMS system) """
    def __unicode__(self):
        return "%s (%d)" % (self.name, self.number)
        
    class Meta:
        verbose_name = 'Email Box'
        ordering = ['number']
    
    name = models.CharField("Name", max_length=255)
    number = models.IntegerField("Number")


class Person(models.Model):
    """ A sender or recipient of emails """
    def __unicode__(self):
        return "%s (%s) [%d]" % (self.name, self.alias, self.id)
        
    class Meta:
        verbose_name = 'Person'
        ordering = ['-name']
    
    name = models.CharField("Name", max_length=255, blank=True, default='')
    name_hash = models.CharField("Name", max_length=255, blank=True, default='')    
    alias = models.CharField("Alias", max_length=255, blank=True, default='')

class Thread(models.Model):
    """ An email thread """
    def __unicode__(self):
        return "%s (%d)" % (self.name, self.count)
        
    class Meta:
        verbose_name = "Email Thread"
        ordering = ['name']
    
    name = models.CharField("Name", max_length=255)
    date = models.DateTimeField("Date")
    count = models.IntegerField("Email Count")
    avg_interval = models.DecimalField("Average Interval", max_digits=10, decimal_places=3, blank=True, null=True)
    max_interval = models.DecimalField("Maximum Interval", max_digits=10, decimal_places=3, blank=True, null=True)
    min_interval = models.DecimalField("Minimum Interval", max_digits=10, decimal_places=3, blank=True, null=True)
    
class EmailManager(models.Manager):

    def _compile_re(self, d, abbrev):
        for k in d:
            d[k] = re.compile(d[k].replace('_XX_', abbrev))
        return d

    def __init__(self):
        self.count = 0 # target looks to be 4777; email splitting currently at 4766
        self.success = 0
        self.failure = 0
        
        name_chars = r''
        self.re_gremlins = re.compile(r'[\xb7\xab\xa2\xbb\xa3\xae\xa5]')
        self.re_non_alpha = re.compile(r'[^A-Z]')
        self.re_re = re.compile(r'([^\s]*re\:\s?)+', re.I)
        self.re_to = {
            'detector': r'^.?\s*.?_XX_:',
            'first': r'([\w\s\.\'\-]+)\s+\(?\s*[cC]N[\~;:=]([\w\s\.\'\-]+[=\/])',
            'second': r'^.?\s*.?_XX_:\s+([A-Za-z_\s\.\'\-]+)\s{3,}',
            'third': r'^.?\s*.?_XX_:\s+([A-Za-z_\s\.\'\-]+)\s+\(',
            'fourth': r'^.?\s*.?_XX_:\s+([A-Za-z_\s\.\'\-]+)',
            'alias_ats': r'^.?\s*.?_XX_:\s+([A-Z_\s]+)\s+\([\w\@]',   
            'combo': r'([\w\s\.\'\-]+)\s{3,}([A-Z_\s]+)'         
        }
        self.re_cc = {
            'detector': self.re_to['detector'],
        }
        self.re_bcc = {
            'detector': self.re_to['detector'],
        }

        self.re_to = self._compile_re(self.re_to, 'TO')
        self.re_cc = self._compile_re(self.re_cc, 'CC')
        self.re_bcc = self._compile_re(self.re_bcc, 'BCC')

        self.re_subject = re.compile(r'^\s*.?SUBJECT:(.*)')
        self.re_creation_date = re.compile(r'CREATI(O|0|o\.)N\s+[DO]ATE[j\/\!]TIME:(.+)')
        self.re_attachment_start = re.compile(r'^([^=;]*)[=;\s]{5,}ATTACHMENT')
        self.re_attachment_end = re.compile(r'^([^=;]*)[=;\s]{5,}END\s+ATTACHMENT')        
        
        super(EmailManager, self).__init__()

    def _make_name_hash(self, t):
        return self.re_non_alpha.sub('',t.strip().upper())

    def _make_subject_hash(self, t):
        return self.re_re.sub('', t.strip())

    def _extract_person(self, line):
        line_s = line.strip().replace('"','')
        name = None
        alias = None
        m = self.re_to['first'].search(line_s)
        if m is not None:
            name = m.group(1).strip()
        else:
            m = self.re_to['second'].search(line_s)
            if m is not None:
                if m.group(1).strip().upper()==m.group(1).strip():
                    alias = m.group(1).strip()
                else:
                    name = m.group(1).strip()
            else:
                m = self.re_to['third'].search(line_s)
                if m is not None:
                    if m.group(1).strip().upper()==m.group(1).strip():
                        alias = m.group(1).strip()
                    else:
                        name = m.group(1).strip()
                else:
                    m = self.re_to['fourth'].search(line_s)
                    if m is not None:
                        if m.group(1).strip().upper()==m.group(1).strip():
                            alias = m.group(1).strip()
                        else:
                            name = m.group(1).strip()
                    else:
                        m = self.re_to['alias_ats'].search(line_s)
                        if m is not None:
                            alias = m.group(1).strip()
              
        p = None
        if name:
            m = self.re_to['combo'].search(name)
            if m is not None:
                name = m.group(1).strip()
                alias = m.group(2).strip()
        
            (p, created) = Person.objects.get_or_create(name=name, defaults={'alias': (alias is not None) and alias or '', 'name_hash': self._make_name_hash(name)})
            if (not created) and len(p.alias)==0 and alias:
                p.alias = alias
                p.save()
            
            return p
            
        elif alias:
            try:
                (p, created) = Person.objects.get_or_create(alias=alias)
            except Person.MultipleObjectsReturned, e:
                p = Person.objects.filter(alias=alias)[0]
            return p
            
        else:
            return None
            self.failure += 1
                        
    def _zap_gremlins(self, t):
        return self.re_gremlins.sub("", t)
          
    
    def _clean_date(self, t):
    
        def _trans(d):
            return d.replace('199S','1998').replace('199B','1998').replace('l', '1').replace('i','1').replace('I','1').replace('B', '8').replace('O', '0').replace('S', '5')
        t = t.replace('0CT', 'OCT').replace('5EP', 'SEP').replace('~', '-').replace("'",'').replace(': ',':')
        parts = t.split('-')
        parts[0] = _trans(parts[0])
        if len(parts)>=3:
            parts[2] = _trans(parts[2])
        t = '-'.join(parts)
        return t
  
    def parse_text(self, filename, lines, store=False):
        self.count += 1

        if store:
            f = open('parsed/source/%d.txt' % self.count, 'w')
            f.write("".join(lines))
            f.close()
        
        candidate_date = ''
        found_to = False
        found_date = False
        found_subject = False
        found_text = False
        collecting_text = False
        collecting_attachment = False
        
        E = Email()
        E_to = []
        E_cc = []
        E.source = unicode(self._zap_gremlins("".join(lines)), 'utf-8')
        
        for line in lines:

            # to
            if (not found_to) and (self.re_to['detector'].search(line) is not None):
                p = self._extract_person(line)
                if p is not None:
                    E_to.append(p)
                    found_to = True

            # cc
            if self.re_cc['detector'].search(line) is not None:
                p = self._extract_person(line)
                if p is not None:
                    E_cc.append(p)

            # creation date/time
            m = self.re_creation_date.search(line)
            if (not found_date) and (m is not None):
                candidate_date = m.group(2).strip()
                candidate_date = self._clean_date(candidate_date)
                try:
                    E.creation_date_time = parser.parse(candidate_date)
                    found_date = True
                except:
                    pass

            # subject
            m = self.re_subject.search(line)
            if (not found_subject) and (m is not None):
                E.subject = unicode(self._zap_gremlins(m.group(1).strip()), 'utf-8')
                E.subject_hash = self._make_subject_hash(E.subject)
                found_subject = True
            
            # text
            if line.strip()=="TEXT:":
                collecting_text = True
                found_text = True
            
            # attachment
            m = self.re_attachment_start.search(line)
            if m is not None:
                collecting_text = False
                collecting_attachment = True
                E.text += unicode(self._zap_gremlins(m.group(1)), 'utf-8')
            
            # end of attachment    
            if self.re_attachment_end.search(line) is not None:
                collecting_attachment = False
                
            if collecting_text:                
                E.text += unicode(self._zap_gremlins(line), 'utf-8')
                
            if collecting_attachment:
                E.attachment += unicode(self._zap_gremlins(line), 'utf-8')
                
                
        if found_to and found_subject and found_text and found_date:            
            E.subject = E.subject.strip()
            E.text = E.text.strip()
            E.attachment = E.attachment.strip()
            
            try:
                E.save()
            except Exception, e:                
                print str(E.source)
                raise e

            E.to = E_to
            E.cc = E_cc
            E.save()

            self.success += 1

            return True

        else:
            f = open('parsed/failures/%s.error' % filename, 'w')
            f.write("found_to: %s\n" % str(found_to))
            f.write("found_subject: %s\n" % str(found_subject))
            f.write("found_text: %s\n" % str(found_text))
            f.write("found_date: %s\n" % str(found_date))
            f.write("candidate date: %s\n\n" % candidate_date)
            f.write(E.source)
            f.close()
            
            return False
        

class Email(models.Model):
    """ An email """
    def __unicode__(self):
        return '%s (%s)' % (self.subject, self.creation_date_time)
        
    class Meta:
        verbose_name = 'Email'
        ordering = ['-creation_date_time']
        
    box = models.ForeignKey(Box, blank=True, null=True)
    record_type = models.CharField("Record Type", max_length=200, default='', blank=True)
    creator = models.ForeignKey(Person, related_name='creators', blank=True, null=True)
    creation_date_time = models.DateTimeField("Creation Date/Time", db_index=True, blank=True, null=True)
    subject = models.CharField("Subject", max_length=255, default='', blank=True)
    subject_hash = models.CharField("Subject Hash", max_length=255, default='', blank=True)
    to = models.ManyToManyField(Person, related_name='to', blank=True)
    cc = models.ManyToManyField(Person, null=True, related_name='cc')
    text = models.TextField('Text', default='', blank=True)
    attachment = models.TextField('Attachment', default='', blank=True)
    source = models.TextField('Source', default='', blank=True)

    email_thread = models.ForeignKey('Thread', null=True, blank=True)
    in_reply_to = models.ForeignKey('Email', null=True, blank=True)

    objects = EmailManager()

        
