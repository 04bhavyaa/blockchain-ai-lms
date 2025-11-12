"""
Django admin configuration for admin service - ENHANCED VERSION
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import AdminDashboardLog, FraudDetectionLog, AdminSettings, SystemMetrics


@admin.register(AdminDashboardLog)
class AdminDashboardLogAdmin(admin.ModelAdmin):
    list_display = ['admin_user', 'action_type_colored', 'target_type', 'created_at']
    list_filter = ['action_type', 'target_type', 'created_at']
    search_fields = ['admin_user__email', 'description']
    readonly_fields = ['created_at', 'ip_address']
    date_hierarchy = 'created_at'
    
    @admin.display(description='Action Type')
    def action_type_colored(self, obj):
        colors = {
            'user_created': 'green',
            'user_updated': 'blue',
            'user_banned': 'red',
            'user_deleted': 'darkred',
            'course_approved': 'green',
            'course_rejected': 'orange',
            'fraud_detected': 'red',
        }
        color = colors.get(obj.action_type, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_type_display()
        )


@admin.register(FraudDetectionLog)
class FraudDetectionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'fraud_type', 'status_colored', 'severity_badge', 'created_at']
    list_filter = ['fraud_type', 'status', 'severity', 'created_at']
    search_fields = ['user__email', 'description']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    fieldsets = (
        ('Basic Info', {'fields': ('user', 'fraud_type', 'severity')}),
        ('Details', {'fields': ('description', 'evidence', 'ip_address', 'user_agent')}),
        ('Review', {'fields': ('reviewed_by', 'status', 'action_taken', 'resolved_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    @admin.display(description='Status')
    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'under_review': 'blue',
            'resolved': 'green',
            'false_positive': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description='Severity')
    def severity_badge(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#dc3545',
            'critical': '#6f0000'
        }
        color = colors.get(obj.severity, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.severity.upper()
        )


@admin.register(AdminSettings)
class AdminSettingsAdmin(admin.ModelAdmin):
    list_display = ['setting_key', 'setting_type', 'last_updated_by', 'updated_at']
    list_filter = ['setting_type', 'updated_at']
    search_fields = ['setting_key', 'description']
    readonly_fields = ['updated_at']


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ['recorded_at', 'total_users', 'total_courses', 'total_revenue_formatted']
    list_filter = ['recorded_at']
    readonly_fields = [
        'total_users', 'total_courses', 'total_enrollments',
        'total_tokens_distributed', 'total_revenue', 'recorded_at'
    ]
    date_hierarchy = 'recorded_at'
    
    @admin.display(description='Total Revenue')
    def total_revenue_formatted(self, obj):
        return format_html(
            '<span style="color: green; font-weight: bold;">${:,.2f}</span>',
            float(obj.total_revenue)
        )
