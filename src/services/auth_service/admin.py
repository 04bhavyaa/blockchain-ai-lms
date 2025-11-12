"""
Django admin configuration for auth service
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    EmailVerificationToken, PasswordResetToken, WalletConnection, 
    LoginAttempt, AuthSession
)


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_used', 'created_at', 'expires_at', 'is_expired_display']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at', 'used_at', 'expires_at']
    
    @admin.display(boolean=True, description='Expired')
    def is_expired_display(self, obj):
        return obj.is_expired()


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_used', 'created_at', 'expires_at', 'is_expired_display']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at', 'used_at', 'expires_at']
    
    @admin.display(boolean=True, description='Expired')
    def is_expired_display(self, obj):
        return obj.is_expired()


@admin.register(WalletConnection)
class WalletConnectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'wallet_address_short', 'network', 'is_verified', 'connected_at', 'last_verified_at']
    list_filter = ['network', 'is_verified', 'connected_at']
    search_fields = ['user__email', 'wallet_address']
    readonly_fields = ['connected_at', 'last_verified_at', 'wallet_address', 'verification_signature']
    
    @admin.display(description='Wallet Address')
    def wallet_address_short(self, obj):
        if obj.wallet_address:
            return format_html(
                '<code>{}</code>',
                f"{obj.wallet_address[:6]}...{obj.wallet_address[-4:]}"
            )
        return "-"


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'ip_address', 'status_colored', 'attempted_at']
    list_filter = ['status', 'attempted_at']
    search_fields = ['user__email', 'email', 'ip_address']
    readonly_fields = ['attempted_at', 'failure_reason']
    date_hierarchy = 'attempted_at'
    
    @admin.display(description='Status')
    def status_colored(self, obj):
        colors = {
            'success': 'green',
            'failed': 'red',
            'blocked': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )


@admin.register(AuthSession)
class AuthSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'is_active_colored', 'created_at', 'last_activity', 'expires_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'ip_address', 'token']
    readonly_fields = ['created_at', 'last_activity', 'expires_at', 'token']
    actions = ['deactivate_sessions']
    
    @admin.display(description='Active')
    def is_active_colored(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    
    @admin.action(description='Deactivate selected sessions')
    def deactivate_sessions(self, request, queryset):
        count = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, f'{count} sessions deactivated')
