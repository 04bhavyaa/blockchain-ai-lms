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
import logging

from django.conf import settings

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
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Create verification token
        verification = EmailVerificationToken.create_token(user)
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
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = request.data.get('password')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            LoginAttempt.objects.create(
                user=None,
                email=email,
                ip_address=get_client_ip(request),
                status="failed"
            )
            raise AuthenticationError("User does not exist")
        # Verify password
        if not user.check_password(password):
            LoginAttempt.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                status="failed"
            )
            raise AuthenticationError("Invalid password")
        if user.is_banned:
            raise AuthenticationError(f"Account banned. Reason: {user.banned_reason}")
        if not user.is_verified:
            # In development, allow login if email sending is disabled or failed
            email_user = getattr(settings, 'EMAIL_HOST_USER', '')
            email_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
            if settings.DEBUG and (not email_user or not email_password):
                # Auto-verify in development mode if email is not properly configured
                logger.warning(f"Auto-verifying user {user.email} in DEBUG mode (email not properly configured)")
                user.is_verified = True
                user.email_verified_at = timezone.now()
                user.save()
            else:
                raise ValidationError("Email not verified. Please check your inbox or use 'Resend Verification' below.")
        # Record login
        LoginAttempt.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            status="success"
        )
        refresh = RefreshToken.for_user(user)
        expires_in = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
        response_data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': ProfileSerializer(user).data,
            'expires_in': expires_in
        }
        logger.info(f"User logged in: {user.email}")
        return Response({
            'status': 'success',
            'message': 'Login successful',
            'data': response_data
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        logger.info(f"User logged out: {request.user.email}")
        return Response({
            'status': 'success',
            'message': 'Logout successful'
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        serializer = ProfileSerializer(request.user)
        return Response({'status': 'success', 'data': serializer.data})

    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
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
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        # Verify old password
        if not user.check_password(request.data.get('old_password')):
            raise AuthenticationError("Old password is incorrect")
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        logger.info(f"Password changed: {user.email}")
        return Response({
            'status': 'success',
            'message': 'Password changed successfully'
        })

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def forgot_password(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ResourceNotFoundError("No account for this email.")
        reset_token = PasswordResetToken.create_token(user)
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
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_obj = PasswordResetToken.objects.get(token=request.data['token'])
        if token_obj.is_expired():
            raise ValidationError("Reset token has expired")
        user = token_obj.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
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
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_obj = EmailVerificationToken.objects.get(token=request.data['token'])
        if token_obj.is_expired():
            raise ValidationError("Verification token has expired")
        user = token_obj.user
        user.is_verified = True
        user.email_verified_at = timezone.now()
        user.save()
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
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ResourceNotFoundError("User not found")
        if user.is_verified:
            raise ValidationError("Email already verified")
        EmailVerificationToken.objects.filter(user=user).delete()
        verification = EmailVerificationToken.create_token(user)
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
        serializer = ConnectWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet_address = serializer.validated_data['wallet_address'].lower()
        signature = serializer.validated_data['signature']
        network = serializer.validated_data.get('network', 'sepolia')
        # Prevent wallet re-use
        if WalletConnection.objects.filter(wallet_address=wallet_address).exclude(user=request.user).exists():
            raise ConflictError("Wallet already connected to another account")
        # Signature verification stub (needs actual Web3 code for production)
        # message = f"Connect wallet: {wallet_address}"
        # signer_address = w3.eth.account.recover_message(message, signature=signature)
        # if signer_address.lower() != wallet_address:
        #     raise ValidationError("Invalid wallet signature")
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
        if not request.user.wallet_address:
            raise ValidationError("Wallet not connected")
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
        request.user.wallet_address = None
        request.user.save()
        WalletConnection.objects.filter(user=request.user).delete()
        logger.info(f"Wallet disconnected: {request.user.email}")
        return Response({
            'status': 'success',
            'message': 'Wallet disconnected successfully'
        })
