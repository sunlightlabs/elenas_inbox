import datetime
from haystack.indexes import *
from haystack import site
from mail.models import *


class ThreadIndex(SearchIndex):
    text = CharField(document=True)
    to = MultiValueField(null=True)
    date = DateField(model_attr='date', null=True)
    text_and_recipients = CharField(null=True)
    
    def prepare_to(self, object):
        recipients = []
        for email in Email.objects.filter(email_thread=object):
            for recipient in email.to.values():
                recipients.append((len(recipient['name'].strip())>0) and recipient['name'] or recipient['alias'])
            for recipient in email.cc.values():
                recipients.append((len(recipient['name'].strip())>0) and recipient['name'] or recipient['alias'])
        return recipients
    
    def prepare_text(self, object):
        text = ''
        for email in Email.objects.filter(email_thread=object):
            text += "%s %s" % (email.subject, email.text)
        return text
            
    
    def prepare_text_and_recipients(self, object):
        return "%s %s" % (" ".join(self.prepare_to(object)), self.prepare_text(object))

    def prepare_date(self, object):
        if object.date.year<1900:
            return None
        else:
            return object.date

    def get_queryset(self):
        """Used when the entire index for model is updated."""
        return Thread.objects.all()

site.register(Thread, ThreadIndex)
