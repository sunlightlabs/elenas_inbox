from django.db import models
from settings import *
import re


class Box(models.Model):
    """ An email 'box' (as defined by the ARMS system) """
    def __unicode__(self):
        return "%s (%d)" % (self.name, self.number)
        
    class Meta:
        verbose_name = 'Email Box'
        ordering = 'number'
    
    name = models.CharField("Name", max_length_255)
    number = models.IntegerField("Number", max_digits=3)


class Person(models.Model):
    """ A sender or recipient of emails """
    def __unicode__(self):
        return self.name
        
    class Meta:
        verbose_name = 'Person'
        ordering = ['-name']
        
    name = models.CharField("Name", max_length=255)

class Thread(models.Model):
    """ An email thread """
    def __unicode__(self):
        return self.name
        
    class Meta:
        verbose_name = "Email Thread"
        ordering = 'name'
    
    name = models.CharField("Name", max_length=255)
    
class EmailManager(models.Manager):
    def __init__(self):
        super(EmailManager, self).__init__()

    def parse_email_text(self, text):
        
        pass
        

class Email(models.Model):
    """ An email """
    def __unicode__(self):
        return '%s (%s)' % (self.subject, self.creation_date_time)
        
    class Meta:
        verbose_name = 'Email'
        ordering = ['-creation_date_time']
        
    box = models.ForeignKey(Box)
    record_type = models.CharField("Record Type", max_length=200, default='', blank=True)
    creator = models.ForeignKey(Person)
    creation_date_time = models.DateTime("Creation Date/Time", db_index=True)
    subject = models.CharField("Subject", max_length=255)
    to = models.ManyToManyField(Person)
    cc = models.ManyToManyField(Person, null=True)
    bcc = models.ManyToManyField(Person, null=True)
    read_date_time = models.DateTimeField("Read Date/Time")
    text = models.TextField('Text', default='', blank=True)
    attachment = models.TextField('Attachment', default='', blank=True)
    email_thread = models.ForeignKey('Thread')
    in_reply_to = models.ForeignKey('Email')

    objects = EmailManager()

        
