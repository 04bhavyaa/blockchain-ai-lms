"""
Admin service models for dashboard, monitoring, and management
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AdminDashboardLog(models.Model):
    """Log of all admin activities for audit trail"""
    
    ACTION_TYPES = [
        ('user_created', 'User Created'),
        ('user_updated', 'User Updated'),
        ('user_banned', 'User Banned'),
        ('user_deleted', 'User Deleted'),
        ('course_approved', 'Course Approved'),
        ('course_rejected', 'Course Rejected'),
        ('course_deleted', 'Course Deleted'),
        ('token_distributed', 'Token Distributed'),
        ('payment_refunded', 'Payment Refunded'),
        ('certificate_verified', 'Certificate Verified'),
        ('fraud_detected', 'Fraud Detected'),
        ('settings_updated', 'Settings Updated'),
    ]
    
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_logs')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    target_type = models.CharField(max_length=50)  # 'user', 'course', 'payment', etc.
    target_id = models.IntegerField()
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['admin_user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.admin_user} - {self.action_type} - {self.target_type}({self.target_id})"


class FraudDetectionLog(models.Model):
    """Log for detecting fraudulent activities"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('confirmed', 'Confirmed Fraud'),
        ('false_positive', 'False Positive'),
        ('resolved', 'Resolved'),
    ]
    
    FRAUD_TYPES = [
    ('multiple_accounts', 'Multiple Accounts'),
    ('token_manipulation', 'Token Manipulation'),
    ('payment_chargeback', 'Payment Chargeback'),
    ('suspicious_login', 'Suspicious Login'),
    ('fake_certificates', 'Fake Certificates'),
    ('unauthorized_access', 'Unauthorized Access'),
    ('bot_activity', 'Bot Activity'),
    ('brute_force', 'Brute Force Attack'),
    ('abnormal_activity', 'Abnormal Activity'),
    ('payment_fraud', 'Payment Fraud'),
    ('wallet_manipulation', 'Wallet Manipulation'),
    ('token_farming', 'Token Farming'),
    ]

    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='fraud_logs')
    fraud_type = models.CharField(max_length=50, choices=FRAUD_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    severity = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='medium'
    )
    description = models.TextField()
    evidence = models.JSONField(default=dict)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='fraud_reviewed')
    action_taken = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'fraud_detection_logs'
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.fraud_type} ({self.status})"


class AdminSettings(models.Model):
    """Global admin settings and configurations"""
    
    SETTING_TYPES = [
        ('token_reward', 'Token Reward'),
        ('payment_config', 'Payment Configuration'),
        ('blockchain_config', 'Blockchain Configuration'),
        ('email_config', 'Email Configuration'),
        ('rate_limit', 'Rate Limiting'),
    ]
    
    setting_key = models.CharField(max_length=100, unique=True)
    setting_type = models.CharField(max_length=50, choices=SETTING_TYPES)
    value = models.JSONField()
    description = models.TextField(blank=True)
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_settings')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_settings'
        ordering = ['setting_key']
    
    def __str__(self):
        return f"{self.setting_key} ({self.setting_type})"


class SystemMetrics(models.Model):
    """Store system performance metrics"""
    
    total_users = models.IntegerField(default=0)
    total_courses = models.IntegerField(default=0)
    total_enrollments = models.IntegerField(default=0)
    total_tokens_distributed = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    active_users_today = models.IntegerField(default=0)
    active_users_week = models.IntegerField(default=0)
    active_users_month = models.IntegerField(default=0)
    total_lessons_completed = models.IntegerField(default=0)
    average_course_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    platform_uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'system_metrics'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['-recorded_at']),
        ]
    
    def __str__(self):
        return f"Metrics - {self.recorded_at}"
