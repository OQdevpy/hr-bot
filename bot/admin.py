from django.contrib import admin
from .models import Registration

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'telegram_username', 'phone_number', 'registration_time')
    search_fields = ('full_name', 'telegram_username', 'phone_number', 'about')
    list_filter = ('registration_time',)
    readonly_fields = ('registration_time',)