from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from .models import *

# Register your models here.
admin.site.register(Enif_User, UserAdmin)
admin.site.register(Permission)
admin.site.register(Whitelist)
admin.site.register(Intent)
admin.site.register(Stopword)
admin.site.register(Pattern)
admin.site.register(Enif_Session)
admin.site.register(Enif_Request)
admin.site.register(Enif_Intent_Answer)
admin.site.register(Enif_System_Answer)
admin.site.register(Enif_Session_History)
admin.site.register(Invoices)
