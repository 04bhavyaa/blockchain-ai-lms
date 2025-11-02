"""
Django admin configuration for auth service
"""

from django.contrib import admin
from .models import (
    EmailVerificationToken, PasswordResetToken, WalletConnection, LoginAttempt, AuthSession
)

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at', 'used_at', 'expires_at']

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at', 'used_at', 'expires_at']

@admin.register(WalletConnection)
class WalletConnectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'wallet_address', 'network', 'is_verified', 'connected_at', 'last_verified_at']
    list_filter = ['network', 'is_verified', 'connected_at']
    search_fields = ['user__email', 'wallet_address']
    readonly_fields = ['connected_at', 'last_verified_at', 'wallet_address']

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'ip_address', 'status', 'attempted_at']
    list_filter = ['status', 'attempted_at']
    search_fields = ['user__email', 'email', 'ip_address']
    readonly_fields = ['attempted_at']
    date_hierarchy = 'attempted_at'

@admin.register(AuthSession)
class AuthSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'is_active', 'created_at', 'last_activity', 'expires_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'ip_address', 'token']
    readonly_fields = ['created_at', 'last_activity', 'expires_at', 'token']
