"""
Custom permission classes
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow owners of an object to edit it"""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions for object owner
        return obj.user == request.user


class IsInstructor(permissions.BasePermission):
    """Allow only instructors"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsVerified(permissions.BasePermission):
    """Allow only verified users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_verified


class IsNotBanned(permissions.BasePermission):
    """Allow only non-banned users"""
    
    def has_permission(self, request, view):
        return request.user and not request.user.is_banned
