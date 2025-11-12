"""
User service views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import logging

from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer,
    UpdateProfileSerializer, ConnectWalletSerializer,
    ChangePasswordSerializer
)
from src.shared.exceptions import ValidationError, AuthenticationError

User = get_user_model()
logger = logging.getLogger(__name__)


class UserViewSet(viewsets.GenericViewSet):
    """User management viewset"""
    queryset = User.objects.all()
    
    def get_permissions(self):
        if self.action in ['register', 'login']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'register':
            return UserRegistrationSerializer
        elif self.action == 'update_profile':
            return UpdateProfileSerializer
        elif self.action == 'connect_wallet':
            return ConnectWalletSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserProfileSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register new user"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Login user"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            raise ValidationError("Email and password required")
        
        user = authenticate(request, username=email, password=password)
        
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        if user.is_banned:
            raise AuthenticationError(f"Account banned: {user.banned_reason}")
        
        # Update last login
        from django.utils import timezone
        user.last_login_at = timezone.now()
        user.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'status': 'success',
            'data': {
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
            }
        })
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        serializer = UserProfileSerializer(request.user)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update user profile"""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Profile updated successfully',
            'data': UserProfileSerializer(request.user).data
        })
    
    @action(detail=False, methods=['post'])
    def connect_wallet(self, request):
        """Connect Web3 wallet"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        request.user.wallet_address = serializer.validated_data['wallet_address']
        request.user.save()
        
        logger.info(f"Wallet connected for user {request.user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Wallet connected successfully',
            'data': UserProfileSerializer(request.user).data
        })
    
    @action(detail=False, methods=['post'])
    def disconnect_wallet(self, request):
        """Disconnect Web3 wallet"""
        request.user.wallet_address = None
        request.user.save()
        
        logger.info(f"Wallet disconnected for user {request.user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Wallet disconnected successfully'
        })
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            raise ValidationError("Old password is incorrect")
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        logger.info(f"Password changed for user {user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Password changed successfully'
        })
    
    @action(detail=False, methods=['get'])
    def token_balance(self, request):
        """Get user token balance"""
        return Response({
            'status': 'success',
            'data': {
                'token_balance': request.user.token_balance
            }
        })
