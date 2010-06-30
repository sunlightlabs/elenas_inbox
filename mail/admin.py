from django.contrib import admin
from mail.models import *

class PersonAdmin(admin.ModelAdmin):
    list_filter = ('is_merged',)
    prepopulated_fields = {"slug": ("name",)}
    
class ThreadAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    
    
admin.site.register(Person, PersonAdmin)
admin.site.register(Box)
admin.site.register(Email)
admin.site.register(Thread, ThreadAdmin)