"""
Base serializers and mixins for all services
"""

from rest_framework import serializers


class BaseResponseSerializer(serializers.Serializer):
    """Base response serializer for all API responses"""
    status = serializers.CharField()
    data = serializers.JSONField()
    message = serializers.CharField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Error response serializer"""
    status = serializers.CharField()
    error_code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(required=False)


class PaginationSerializer(serializers.Serializer):
    """Pagination info serializer"""
    count = serializers.IntegerField()
    next = serializers.URLField(required=False, allow_null=True)
    previous = serializers.URLField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False)
    page_size = serializers.IntegerField(required=False)
    total_pages = serializers.IntegerField(required=False)


class TimestampedSerializer(serializers.Serializer):
    """Mixin for models with created_at and updated_at"""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
