from django.contrib import admin
from django.utils.html import format_html
from .models import Client, Mailing, Message, MailingLog


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['full_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'frequency', 'start_time', 'end_time', 'created_by', 'created_at']
    list_filter = ['status', 'frequency', 'created_at', 'start_time']
    search_fields = ['title', 'subject']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['clients']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['mailing', 'client', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['mailing__title', 'client__email', 'client__full_name']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('mailing', 'client')


@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    list_display = ['mailing', 'level', 'message', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['mailing__title', 'message']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('mailing') 