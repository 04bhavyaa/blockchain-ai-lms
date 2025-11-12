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
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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

@method_decorator(csrf_exempt, name='dispatch')
class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints - CSRF exempt since using JWT"""
    
    # Override default permission to allow public endpoints
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            
            # Log the incoming data for debugging
            logger.debug(f"Registration data received: {request.data}")
            
            if not serializer.is_valid():
                # Return detailed validation errors
                logger.error(f"Registration validation errors: {serializer.errors}")
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = serializer.save()
            
            # Delete any existing verification token before creating new one
            EmailVerificationToken.objects.filter(user=user).delete()
            
            # Create verification token
            verification = EmailVerificationToken.create_token(user)
            verification_link = f"{settings.FRONTEND_URL}/pages/auth/verify-email.html?token={verification.token}"
            
            try:
                send_email(
                    to_email=user.email,
                    subject='Verify Your Email Address',
                    message=f'Click the link to verify your email: {verification_link}',
                    html_message=f'''
                        <h2>Welcome to Blockchain AI LMS!</h2>
                        <p>Thank you for registering! Please click the button below to verify your email address:</p>
                        <a href="{verification_link}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a>
                        <p>Or copy and paste this link into your browser:</p>
                        <p>{verification_link}</p>
                        <p>This link will expire in 24 hours.</p>
                    '''
                )
            except Exception as email_error:
                logger.warning(f"Email sending failed for {user.email}: {str(email_error)}")
                # Continue even if email fails in development
            
            logger.info(f"User registered: {user.email}")
            return Response({
                'status': 'success',
                'message': 'Registration successful. Please verify your email.',
                'data': {'email': user.email}
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            
            logger.debug(f"Login attempt: {request.data.get('email')}")
            
            if not serializer.is_valid():
                logger.error(f"Login validation errors: {serializer.errors}")
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
                return Response({
                    'status': 'error',
                    'message': 'Invalid email or password'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Verify password
            if not user.check_password(password):
                LoginAttempt.objects.create(
                    user=user,
                    ip_address=get_client_ip(request),
                    status="failed"
                )
                return Response({
                    'status': 'error',
                    'message': 'Invalid email or password'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if user.is_banned:
                return Response({
                    'status': 'error',
                    'message': f'Account banned. Reason: {user.banned_reason}'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if not user.is_verified:
                return Response({
                    'status': 'error',
                    'message': 'Email not verified. Please check your inbox for the verification link.',
                    'email': user.email,
                    'needs_verification': True
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Record successful login
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
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        """Resend email verification with rate limiting"""
        email = request.data.get('email')
        
        if not email:
            raise ValidationError("Email is required")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists for security
            return Response({
                'status': 'success',
                'message': 'If the email exists and is unverified, a verification link has been sent'
            })
        
        if user.is_verified:
            raise ValidationError("Email already verified")
        
        # Check for recent verification email (rate limiting - 1 minute)
        recent_token = EmailVerificationToken.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
        ).first()
        
        if recent_token:
            return Response({
                'status': 'error',
                'message': 'Verification email was recently sent. Please wait a minute before requesting another.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Delete old tokens and create new one
        EmailVerificationToken.objects.filter(user=user).delete()
        verification = EmailVerificationToken.create_token(user)
        verification_link = f"{settings.FRONTEND_URL}/pages/auth/verify-email.html?token={verification.token}"
        
        try:
            send_email(
                to_email=user.email,
                subject='Verify Your Email Address',
                message=f'Click the link to verify your email: {verification_link}',
                html_message=f'''
                    <h2>Verify Your Email</h2>
                    <p>Thank you for registering! Please click the button below to verify your email address:</p>
                    <a href="{verification_link}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a>
                    <p>Or copy and paste this link into your browser:</p>
                    <p>{verification_link}</p>
                    <p>This link will expire in 24 hours.</p>
                '''
            )
            logger.info(f"Verification email resent: {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to send verification email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'status': 'success',
            'message': 'Verification email sent. Please check your inbox.'
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
        
        # TODO: Add real signature verification in production
        # from web3 import Web3
        # w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        # message = f"Connect wallet: {wallet_address}"
        # encoded_msg = encode_defunct(text=message)
        # recovered_address = w3.eth.account.recover_message(encoded_msg, signature=signature)
        # if recovered_address.lower() != wallet_address:
        #     raise ValidationError("Invalid wallet signature")
        
        wallet, created = WalletConnection.objects.update_or_create(
            user=request.user,
            defaults={
                'wallet_address': wallet_address,
                'network': network,
                'is_verified': True,  # Set to False in production until signature verified
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
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


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
