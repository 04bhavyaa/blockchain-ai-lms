"""
Authentication service views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    EmailVerificationToken, PasswordResetToken, WalletConnection, LoginAttempt
)
from .serializers import (
    RegisterSerializer, LoginSerializer, ProfileSerializer,
    UpdateProfileSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer,
    EmailVerificationSerializer, WalletConnectionSerializer,
    ConnectWalletSerializer, TokenResponseSerializer
)
from src.shared.utils import send_email, get_client_ip
from src.shared.exceptions import (
    ValidationError, AuthenticationError, ConflictError,
    ResourceNotFoundError
)

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints"""
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register new user"""
        
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Create email verification token
        verification = EmailVerificationToken.create_token(user)
        
        # Send verification email
        verification_link = f"{request.build_absolute_uri('/')}verify-email/{verification.token}"
        send_email(
            to_email=user.email,
            subject='Verify Your Email Address',
            message=f'Click the link to verify your email: {verification_link}',
            html_message=f'<a href="{verification_link}">Verify Email</a>'
        )
        
        logger.info(f"User registered: {user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Registration successful. Please verify your email.',
            'data': {'email': user.email}
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Login user and return JWT tokens"""
        
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = request.data.get('password')
        
        user = User.objects.get(email=email)
        
        # Verify password
        if not user.check_password(password):
            LoginAttempt.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=False
            )
            raise AuthenticationError("Invalid password")
        
        # Check if user is banned
        if user.is_banned:
            raise AuthenticationError(f"Account banned. Reason: {user.banned_reason}")
        
        # Check if email is verified
        if not user.is_verified:
            raise ValidationError("Email not verified. Please check your inbox.")
        
        # Record successful login
        LoginAttempt.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': ProfileSerializer(user).data,
            'expires_in': 24 * 3600  # 24 hours
        }
        
        logger.info(f"User logged in: {user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Login successful',
            'data': response_data
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user"""
        
        # Token invalidation handled by frontend (delete token)
        logger.info(f"User logged out: {request.user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Logout successful'
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Get user profile"""
        
        serializer = ProfileSerializer(request.user)
        return Response({'status': 'success', 'data': serializer.data})
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update user profile"""
        
        serializer = UpdateProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(f"Profile updated: {request.user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Profile updated successfully',
            'data': ProfileSerializer(request.user).data
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change password"""
        
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Verify old password
        if not user.check_password(request.data.get('old_password')):
            raise AuthenticationError("Old password is incorrect")
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        logger.info(f"Password changed: {user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Password changed successfully'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def forgot_password(self, request):
        """Request password reset"""
        
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Create password reset token
        reset_token = PasswordResetToken.create_token(user)
        
        # Send reset email
        reset_link = f"{request.build_absolute_uri('/')}reset-password/{reset_token.token}"
        send_email(
            to_email=user.email,
            subject='Password Reset Request',
            message=f'Click the link to reset your password: {reset_link}',
            html_message=f'<a href="{reset_link}">Reset Password</a>'
        )
        
        logger.info(f"Password reset requested: {user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Password reset link sent to your email'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        """Reset password with token"""
        
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get token object
        token_obj = PasswordResetToken.objects.get(token=request.data['token'])
        user = token_obj.user
        
        # Update password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Mark token as used
        token_obj.is_used = True
        token_obj.used_at = timezone.now()
        token_obj.save()
        
        logger.info(f"Password reset completed: {user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Password reset successful. You can now login.'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_email(self, request):
        """Verify email with token"""
        
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get token object
        token_obj = EmailVerificationToken.objects.get(token=request.data['token'])
        user = token_obj.user
        
        # Mark email as verified
        user.is_verified = True
        user.email_verified_at = timezone.now()
        user.save()
        
        # Mark token as used
        token_obj.is_used = True
        token_obj.used_at = timezone.now()
        token_obj.save()
        
        logger.info(f"Email verified: {user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Email verified successfully'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def resend_verification(self, request):
        """Resend email verification"""
        
        email = request.data.get('email')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ResourceNotFoundError("User not found")
        
        if user.is_verified:
            raise ValidationError("Email already verified")
        
        # Create new verification token
        EmailVerificationToken.objects.filter(user=user).delete()
        verification = EmailVerificationToken.create_token(user)
        
        # Send verification email
        verification_link = f"{request.build_absolute_uri('/')}verify-email/{verification.token}"
        send_email(
            to_email=user.email,
            subject='Verify Your Email Address',
            message=f'Click the link to verify your email: {verification_link}',
            html_message=f'<a href="{verification_link}">Verify Email</a>'
        )
        
        logger.info(f"Verification email resent: {user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Verification email sent'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def connect_wallet(self, request):
        """Connect MetaMask wallet"""
        
        serializer = ConnectWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address'].lower()
        signature = serializer.validated_data['signature']
        network = serializer.validated_data.get('network', 'sepolia')
        
        # Check if wallet already connected
        if WalletConnection.objects.filter(wallet_address=wallet_address).exists():
            raise ConflictError("Wallet already connected to another account")
        
        # Verify signature (simplified - in production use Web3.py)
        # web3.eth.account.recover_message() would be used here
        
        # Create wallet connection
        wallet, created = WalletConnection.objects.update_or_create(
            user=request.user,
            defaults={
                'wallet_address': wallet_address,
                'network': network,
                'is_verified': True,
                'verification_signature': signature,
                'last_verified_at': timezone.now()
            }
        )
        
        # Update user wallet address
        request.user.wallet_address = wallet_address
        request.user.save()
        
        logger.info(f"Wallet connected: {request.user.email} - {wallet_address}")
        
        return Response({
            'status': 'success',
            'message': 'Wallet connected successfully',
            'data': WalletConnectionSerializer(wallet).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def wallet_balance(self, request):
        """Get user's token balance from wallet"""
        
        if not request.user.wallet_address:
            raise ValidationError("Wallet not connected")
        
        # In production, fetch balance from blockchain via Web3.py
        balance = request.user.token_balance
        
        return Response({
            'status': 'success',
            'data': {
                'wallet_address': request.user.wallet_address,
                'balance': str(balance),
                'network': 'sepolia'
            }
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def disconnect_wallet(self, request):
        """Disconnect wallet"""
        
        request.user.wallet_address = None
        request.user.save()
        
        WalletConnection.objects.filter(user=request.user).delete()
        
        logger.info(f"Wallet disconnected: {request.user.email}")
        
        return Response({
            'status': 'success',
            'message': 'Wallet disconnected successfully'
        })
