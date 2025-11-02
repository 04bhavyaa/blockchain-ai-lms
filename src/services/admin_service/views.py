"""
Admin service views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from src.shared import require_admin, log_action
from src.shared.exceptions import PermissionDeniedError, ResourceNotFoundError
from django.contrib.auth import get_user_model

from .models import AdminDashboardLog, FraudDetectionLog, AdminSettings, SystemMetrics
from .serializers import (
    UserDetailSerializer, UserListSerializer, UpdateUserSerializer,
    AdminDashboardLogSerializer, FraudDetectionLogSerializer,
    UpdateFraudStatusSerializer, AdminSettingsSerializer,
    SystemMetricsSerializer, DashboardStatsSerializer
)

User = get_user_model()


class AdminUserViewSet(viewsets.ModelViewSet):
    """Admin user management endpoints"""
    
    queryset = User.objects.all()
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UpdateUserSerializer
        return UserDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """List all users with optional filtering"""
        queryset = self.get_queryset()
        
        # Filters
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(first_name__icontains=search)
            )
        
        is_verified = request.query_params.get('is_verified')
        if is_verified:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        is_banned = request.query_params.get('is_banned')
        if is_banned:
            queryset = queryset.filter(is_banned=is_banned.lower() == 'true')
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status': 'success', 'data': serializer.data})
    
    def retrieve(self, request, *args, **kwargs):
        """Get detailed user info"""
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response({'status': 'success', 'data': serializer.data})
    
    @log_action('user_updated')
    def update(self, request, *args, **kwargs):
        """Update user details"""
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        AdminDashboardLog.objects.create(
            admin_user=request.user,
            action_type='user_updated',
            target_type='user',
            target_id=user.id,
            description=f"Updated user {user.email}",
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=True, methods=['post'])
    @log_action('user_banned')
    def ban_user(self, request, pk=None):
        """Ban a user"""
        user = self.get_object()
        reason = request.data.get('reason', 'No reason provided')
        
        user.is_banned = True
        user.banned_reason = reason
        user.save()
        
        AdminDashboardLog.objects.create(
            admin_user=request.user,
            action_type='user_banned',
            target_type='user',
            target_id=user.id,
            description=f"Banned user {user.email}",
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={'reason': reason}
        )
        
        return Response({'status': 'success', 'message': f"User {user.email} banned successfully"})
    
    @action(detail=True, methods=['post'])
    @log_action('user_updated')
    def unban_user(self, request, pk=None):
        """Unban a user"""
        user = self.get_object()
        user.is_banned = False
        user.banned_reason = None
        user.save()
        
        AdminDashboardLog.objects.create(
            admin_user=request.user,
            action_type='user_updated',
            target_type='user',
            target_id=user.id,
            description=f"Unbanned user {user.email}",
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'status': 'success', 'message': f"User {user.email} unbanned successfully"})
    
    @action(detail=True, methods=['delete'])
    @log_action('user_deleted')
    def delete_user(self, request, pk=None):
        """Delete a user account"""
        user = self.get_object()
        email = user.email
        user.delete()
        
        AdminDashboardLog.objects.create(
            admin_user=request.user,
            action_type='user_deleted',
            target_type='user',
            target_id=pk,
            description=f"Deleted user {email}",
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'status': 'success', 'message': f"User {email} deleted successfully"})
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class AdminLogsViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin activity logs"""
    
    queryset = AdminDashboardLog.objects.all()
    serializer_class = AdminDashboardLogSerializer
    permission_classes = [IsAdminUser]
    
    def list(self, request, *args, **kwargs):
        """List admin logs with filters"""
        queryset = self.get_queryset()
        
        # Filters
        action_type = request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        admin_user = request.query_params.get('admin_user')
        if admin_user:
            queryset = queryset.filter(admin_user_id=admin_user)
        
        target_type = request.query_params.get('target_type')
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status': 'success', 'data': serializer.data})


class FraudDetectionViewSet(viewsets.ModelViewSet):
    """Fraud detection and management"""
    
    queryset = FraudDetectionLog.objects.all()
    serializer_class = FraudDetectionLogSerializer
    permission_classes = [IsAdminUser]
    
    def list(self, request, *args, **kwargs):
        """List fraud cases with filters"""
        queryset = self.get_queryset()
        
        # Filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        severity = request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=True, methods=['post'])
    @log_action('fraud_case_updated')
    def update_status(self, request, pk=None):
        """Update fraud case status"""
        fraud_log = self.get_object()
        serializer = UpdateFraudStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        fraud_log.status = serializer.validated_data['status']
        fraud_log.action_taken = serializer.validated_data.get('action_taken', '')
        fraud_log.reviewed_by = request.user
        
        if serializer.validated_data['status'] == 'resolved':
            fraud_log.resolved_at = timezone.now()
        
        fraud_log.save()
        
        return Response({
            'status': 'success',
            'message': f"Fraud case updated to {fraud_log.get_status_display()}",
            'data': FraudDetectionLogSerializer(fraud_log).data
        })
    
    @action(detail=False, methods=['get'])
    def pending_cases(self, request):
        """Get pending fraud cases"""
        pending = self.get_queryset().filter(status='pending').order_by('-severity', '-created_at')
        serializer = self.get_serializer(pending, many=True)
        return Response({
            'status': 'success',
            'count': pending.count(),
            'data': serializer.data
        })


class AdminSettingsViewSet(viewsets.ModelViewSet):
    """Admin settings management"""
    
    queryset = AdminSettings.objects.all()
    serializer_class = AdminSettingsSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'setting_key'
    
    @action(detail=False, methods=['get'])
    def get_by_type(self, request):
        """Get settings by type"""
        setting_type = request.query_params.get('type')
        if not setting_type:
            return Response(
                {'status': 'error', 'message': 'type parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        settings = self.get_queryset().filter(setting_type=setting_type)
        serializer = self.get_serializer(settings, many=True)
        return Response({'status': 'success', 'data': serializer.data})
    
    @log_action('settings_updated')
    def create(self, request, *args, **kwargs):
        """Create new setting"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(last_updated_by=request.user)
        
        return Response(
            {'status': 'success', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )
    
    @log_action('settings_updated')
    def update(self, request, *args, **kwargs):
        """Update setting"""
        setting = self.get_object()
        serializer = self.get_serializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(last_updated_by=request.user)
        
        return Response({'status': 'success', 'data': serializer.data})


class DashboardStatsViewSet(viewsets.ViewSet):
    """Dashboard statistics endpoint"""
    
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def overview(self, request):
        """Get dashboard overview stats - calculated in real-time"""
        from django.db.models import Count, Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        from src.services.courses_service.models import Course, Enrollment
        from src.services.blockchain_service.models import Certificate
        from src.services.payment_service.models import StripePurchase
        
        try:
            # Calculate stats in real-time from actual data
            total_users = User.objects.count()
            
            # Active users (logged in today)
            today = timezone.now().date()
            active_users_today = User.objects.filter(
                last_login__date=today
            ).count()
            
            total_courses = Course.objects.filter(status='published').count()
            total_enrollments = Enrollment.objects.count()
            
            # Calculate tokens distributed from course progress
            from src.services.progress_service.models import CourseProgress
            total_tokens_distributed = CourseProgress.objects.aggregate(
                total=Sum('tokens_earned')
            )['total'] or 0
            
            # Calculate revenue from successful payments
            total_revenue = StripePurchase.objects.filter(
                status='succeeded'
            ).aggregate(
                total=Sum('amount_usd')
            )['total'] or 0
            
            # Count pending items
            pending_certs = Certificate.objects.filter(status='pending').count()
            pending_fraud = FraudDetectionLog.objects.filter(status='pending').count()
            
            # Recent logs
            recent_logs = AdminDashboardLog.objects.all()[:10]
            
            data = {
                'total_users': total_users,
                'active_users_today': active_users_today,
                'total_courses': total_courses,
                'total_enrollments': total_enrollments,
                'total_tokens_distributed': str(int(total_tokens_distributed)),
                'total_revenue': str(float(total_revenue)),
                'pending_fraud_cases': pending_fraud,
                'pending_certificates': pending_certs,
                'recent_logs': AdminDashboardLogSerializer(recent_logs, many=True).data
            }
            
            serializer = DashboardStatsSerializer(data)
            return Response({'status': 'success', 'data': serializer.data})
        except Exception as e:
            logger.error(f"Error calculating dashboard stats: {str(e)}", exc_info=True)
            # Return defaults on error
            data = {
                'total_users': 0,
                'active_users_today': 0,
                'total_courses': 0,
                'total_enrollments': 0,
                'total_tokens_distributed': '0',
                'total_revenue': '0.00',
                'pending_fraud_cases': 0,
                'pending_certificates': 0,
                'recent_logs': []
            }
            serializer = DashboardStatsSerializer(data)
            return Response({'status': 'success', 'data': serializer.data})
