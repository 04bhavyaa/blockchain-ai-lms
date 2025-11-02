"""
Django admin configuration for custom user model
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'username', 'is_verified', 'is_banned',
        'token_balance', 'wallet_address', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_verified', 'is_banned', 'is_staff',
        'created_at', 'last_login_at'
    ]
    search_fields = ['email', 'username', 'wallet_address']
    readonly_fields = ['created_at', 'updated_at', 'last_login_at']
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'avatar_url', 'bio')
        }),
        ('Education', {
            'fields': ('education_level', 'learning_goals')
        }),
        ('Token Economy', {
            'fields': ('token_balance',)
        }),
        ('Web3', {
            'fields': ('wallet_address',)
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_verified', 'email_verified_at')
        }),
        ('Moderation', {
            'fields': ('is_banned', 'banned_reason', 'banned_at')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2')
        }),
    )
    
    ordering = ['-created_at']
