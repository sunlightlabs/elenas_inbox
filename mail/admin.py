from django.contrib import admin
from mail.models import *

admin.site.register(Box)
admin.site.register(Email)
admin.site.register(Person)
admin.site.register(Thread)