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
        return self.name
        
    class Meta:
        verbose_name = 'Person'
        ordering = ['-name']
    
    name = models.CharField("Name", max_length=255)
    name_hash = models.CharField("Name", max_length=255)    
    alias = models.CharField("Alias", max_length=255)

class Thread(models.Model):
    """ An email thread """
    def __unicode__(self):
        return self.name
        
    class Meta:
        verbose_name = "Email Thread"
        ordering = ['name']
    
    name = models.CharField("Name", max_length=255)
    
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
        self.re_non_alpha = re.compile(r'[^A-Z]')
        self.re_re = re.compile(r'[^\s]re\:?', re.I)
        self.re_to = {
            'detector': r'^.?\s*_XX_:',
            'first': r'([\w\s\.\'\-]+)\s+\(?\s*[cC]N[\~;:=]([\w\s\.\'\-]+[=\/])',
            'second': r'^.?\s*_XX_:\s+([A-Za-z_\s\.\'\-]+)\s{3,}'),
            'third': r'^.?\s*_XX_:\s+([A-Za-z_\s\.\'\-]+)\s+\(',
            'fourth': r'^.?\s*_XX_:\s+([A-Za-z_\s\.\'\-]+)',
            'alias_ats': r'^.?\s*_XX_:\s+([A-Z_\s]+)\s+\([\w\@]',   
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

        self.re_subject = re.compile(r'^\s*SUBJECT:(.*)')
        self.re_creation_date = re.compile(r'CREATION\s+[DO]ATE[j\/]TIME:(.+)')
        self.re_attachment_start = re.compile(r'^([^=;]*)[=;\s]{5,}ATTACHMENT')
        self.re_attachment_end = re.compile(r'^([^=;]*)[=;\s]{5,}END\s+ATTACHMENT')        
        
        super(EmailManager, self).__init__()

    def _make_name_hash(self, t):
        return self.re_non_alpha.sub('',t.strip().upper())

    def _make_subject_hash(self, t):
        return self.re_re.sub('', t.strip().upper())

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
              
         # TODO: return person
        if name:
            m = self.re_to['combo'].search(name)
            if m is not None:
                name = m.group(1).strip()
                alias = m.group(2).strip()
            print "Detected name: '%s' (%s)" % (self._make_name_hash(name), line_s)
        elif alias:
            pass
            print "Detected alias: '%s' (%s)" % (alias, line_s)
        else:
            # print "Found no name for line:\n%s" % line.strip()
            self.failure += 1
                        
                
            
    def parse_text(self, filename, lines, store=False):
        self.count += 1

        if store:
            f = open('parsed/%d.txt' % self.count, 'w')
            f.write("".join(lines))
            f.close()
        
        found_to = False
        found_date = False
        found_subject = False
        found_text = False
        collecting_text = False
        collecting_attachment = False
        
        E = Email()
        E.to = []
        E.cc = []
        E.source = "".join(lines)
        
        for line in lines:

            # to
            if (not found_to) and (self.re_to['detector'].search(line) is not None):
                E.to.append(self._extract_person(line))
                found_to = True

            # cc
            if self.re_cc['detector'].search(line) is not None:
                E.cc.append(self._extract_person(line))

            # creation date/time
            m = self.re_creation_date.search(line)
            if (not found_date) and (m is not None):
                try:
                    E.creation_date_time = parser.parse(m.group(1))
                    found_date = True
                except:
                    pass

            # subject
            m = self.re_subject.search(line)
            if (not found_subject) and (m is not None):
                E.subject = m.group(1).strip()
                E.subject_hash = self._make_subject_hash(E.subject)
                found_subject = True
            
            # text
            if line.strip()=="TEXT:"
                collecting_text = True
                found_text = True
            
            # attachment
            m = self.re_attachment_start.search(line)
            if m is not None:
                collecting_text = False
                collecting_attachment = True
                E.text += m.group(1)
            
            # end of attachment    
            if self.re_attachment_end.search(line) is not None:
                collecting_attachment = False
                
            if collecting_text:
                E.text += line
                
            if collecting_attachment:
                E.attachment += line
            
        if found_to and found_subject and found_text and found_date:
            E.save()
        

class Email(models.Model):
    """ An email """
    def __unicode__(self):
        return '%s (%s)' % (self.subject, self.creation_date_time)
        
    class Meta:
        verbose_name = 'Email'
        ordering = ['-creation_date_time']
        
    box = models.ForeignKey(Box, blank=True)
    record_type = models.CharField("Record Type", max_length=200, default='', blank=True)
    creator = models.ForeignKey(Person, related_name='creators', blank=True)
    creation_date_time = models.DateTimeField("Creation Date/Time", db_index=True, blank=True, null=True)
    subject = models.CharField("Subject", max_length=255, default='', blank=True)
    subject_hash = models.CharField("Subject", max_length=255, default='', blank=True)
    to = models.ManyToManyField(Person, related_name='to', blank=True)
    cc = models.ManyToManyField(Person, null=True, related_name='cc')
    text = models.TextField('Text', default='', blank=True)
    attachment = models.TextField('Attachment', default='', blank=True)
    source = models.TextField('Source', default='', blank=True)

    email_thread = models.ForeignKey('Thread')
    in_reply_to = models.ForeignKey('Email')

    objects = EmailManager()

        
