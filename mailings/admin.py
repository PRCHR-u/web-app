from django.contrib import admin
from django.utils.html import format_html
from .models import Client, Mailing, Message, SentMessage, MailingLog


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
    search_fields = ['title', 'message__subject']  # Corrected search field for subject in Message model
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['clients']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(SentMessage)  # Registered with SentMessage
class SentMessageAdmin(admin.ModelAdmin):  # Renamed from MessageAdmin
    # These list_display and list_filter fields are correct for SentMessage
    list_display = ['mailing', 'client', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['mailing__title', 'client__email', 'client__full_name']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('mailing', 'client')


@admin.register(Message)  # Registered with the Message model (templates)
class MessageAdmin(admin.ModelAdmin):  # New Admin class for message templates
    list_display = ['subject', 'created_by', 'created_at']  # Fields from Message model (templates)
    list_filter = ['created_by', 'created_at']
    search_fields = ['subject', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    list_display = ['mailing', 'level', 'message', 'created_at']
    list_filter = ['level', 'created_at']
    search_fields = ['mailing__title', 'message']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('mailing') 