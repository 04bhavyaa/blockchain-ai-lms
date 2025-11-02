"""
Django admin configuration for admin service
"""

from django.contrib import admin
from .models import AdminDashboardLog, FraudDetectionLog, AdminSettings, SystemMetrics


@admin.register(AdminDashboardLog)
class AdminDashboardLogAdmin(admin.ModelAdmin):
    list_display = ['admin_user', 'action_type', 'target_type', 'created_at']
    list_filter = ['action_type', 'target_type', 'created_at']
    search_fields = ['admin_user__email', 'description']
    readonly_fields = ['created_at', 'ip_address']
    date_hierarchy = 'created_at'


@admin.register(FraudDetectionLog)
class FraudDetectionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'fraud_type', 'status', 'severity', 'created_at']
    list_filter = ['fraud_type', 'status', 'severity', 'created_at']
    search_fields = ['user__email', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'fraud_type', 'severity')}),
        ('Details', {'fields': ('description', 'evidence')}),
        ('Review', {'fields': ('status', 'reviewed_by', 'action_taken')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'resolved_at')}),
    )


@admin.register(AdminSettings)
class AdminSettingsAdmin(admin.ModelAdmin):
    list_display = ['setting_key', 'setting_type', 'updated_by', 'updated_at']
    list_filter = ['setting_type', 'updated_at']
    search_fields = ['setting_key', 'description']
    readonly_fields = ['updated_at']


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ['recorded_at', 'total_users', 'total_courses', 'total_revenue']
    list_filter = ['recorded_at']
    readonly_fields = [
        'total_users', 'total_courses', 'total_enrollments',
        'total_tokens_distributed', 'total_revenue', 'recorded_at'
    ]
    date_hierarchy = 'recorded_at'
