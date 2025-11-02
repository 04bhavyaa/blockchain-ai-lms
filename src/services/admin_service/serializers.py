"""
Admin service serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AdminDashboardLog, FraudDetectionLog, AdminSettings, SystemMetrics

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user info for admin view"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'education_level', 'learning_goals', 'wallet_address',
            'token_balance', 'is_verified', 'is_banned', 'banned_reason',
            'created_at', 'updated_at', 'is_staff', 'is_superuser'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserListSerializer(serializers.ModelSerializer):
    """Simplified user info for list view"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'token_balance', 'is_verified', 'is_banned', 'created_at']


class UpdateUserSerializer(serializers.ModelSerializer):
    """Update user details"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'education_level', 'learning_goals', 'is_banned', 'banned_reason']


class AdminDashboardLogSerializer(serializers.ModelSerializer):
    """Admin activity log serializer"""
    
    admin_email = serializers.CharField(source='admin_user.email', read_only=True)
    
    class Meta:
        model = AdminDashboardLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'ip_address']


class FraudDetectionLogSerializer(serializers.ModelSerializer):
    """Fraud detection log serializer"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    reviewed_by_email = serializers.CharField(source='reviewed_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = FraudDetectionLog
        fields = [
            'id', 'user', 'user_email', 'fraud_type', 'status', 'severity',
            'description', 'evidence', 'reviewed_by', 'reviewed_by_email',
            'action_taken', 'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UpdateFraudStatusSerializer(serializers.Serializer):
    """Update fraud detection status"""
    
    status = serializers.ChoiceField(
        choices=[('confirmed', 'Confirmed'), ('false_positive', 'False Positive'), ('resolved', 'Resolved')]
    )
    action_taken = serializers.CharField(required=False, allow_blank=True)


class AdminSettingsSerializer(serializers.ModelSerializer):
    """Admin settings serializer"""
    
    updated_by_email = serializers.CharField(source='last_updated_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = AdminSettings
        fields = [
            'id', 'setting_key', 'setting_type', 'value', 'description',
            'last_updated_by', 'updated_by_email', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']


class SystemMetricsSerializer(serializers.ModelSerializer):
    """System metrics serializer"""
    
    class Meta:
        model = SystemMetrics
        fields = [
            'id', 'total_users', 'total_courses', 'total_enrollments',
            'total_tokens_distributed', 'total_revenue', 'active_users_today',
            'active_users_week', 'active_users_month', 'total_lessons_completed',
            'average_course_rating', 'platform_uptime_percentage', 'recorded_at'
        ]
        read_only_fields = fields


class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics overview"""
    
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    total_tokens_distributed = serializers.DecimalField(max_digits=20, decimal_places=0)
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_fraud_cases = serializers.IntegerField()
    pending_certificates = serializers.IntegerField()
    recent_logs = AdminDashboardLogSerializer(many=True)
