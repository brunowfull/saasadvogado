from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Lawyer

admin.site.register(Lawyer, UserAdmin)