"""
Authentication service serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from src.shared.validators import validate_email, validate_password as validate_pwd
from .models import EmailVerificationToken, PasswordResetToken, WalletConnection

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 'password',
            'password_confirm', 'education_level', 'learning_goals'
        ]

    def validate_email(self, value):
        validate_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def validate_password(self, value):
        try:
            validate_pwd(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        """Validate password confirmation"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=validated_data['password'],
            education_level=validated_data.get('education_level'),
            learning_goals=validated_data.get('learning_goals', [])
        )
        return user

class LoginSerializer(serializers.Serializer):
    """User login serializer"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    remember_me = serializers.BooleanField(required=False, default=False)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User not found")
        return value

class ProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'education_level', 'learning_goals', 'wallet_address',
            'token_balance', 'avatar_url', 'is_verified', 'is_banned',
            'is_staff', 'is_superuser',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'token_balance', 'created_at', 'updated_at', 'is_staff', 'is_superuser']

class UpdateProfileSerializer(serializers.ModelSerializer):
    """Update user profile serializer"""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'education_level',
            'learning_goals', 'avatar_url'
        ]

class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        try:
            validate_pwd(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        """Validate passwords match"""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("New passwords do not match")
        return data

class ForgotPasswordSerializer(serializers.Serializer):
    """Forgot password request serializer"""
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User not found")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    """Reset password with token serializer"""
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        try:
            validate_pwd(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        try:
            token_obj = PasswordResetToken.objects.get(token=data['token'])
            if token_obj.is_expired():
                raise serializers.ValidationError("Token has expired")
            if token_obj.is_used:
                raise serializers.ValidationError("Token already used")
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token")
        return data

class EmailVerificationSerializer(serializers.Serializer):
    """Email verification serializer"""
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            token_obj = EmailVerificationToken.objects.get(token=value)
            if token_obj.is_expired():
                raise serializers.ValidationError("Token has expired")
            if token_obj.is_used:
                raise serializers.ValidationError("Token already used")
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token")
        return value

class WalletConnectionSerializer(serializers.ModelSerializer):
    """Wallet connection serializer"""
    class Meta:
        model = WalletConnection
        fields = [
            'id', 'wallet_address', 'network', 'is_verified',
            'connected_at', 'last_verified_at'
        ]
        read_only_fields = ['id', 'connected_at', 'last_verified_at']

class ConnectWalletSerializer(serializers.Serializer):
    """Connect wallet request serializer"""
    wallet_address = serializers.CharField(max_length=42)
    signature = serializers.CharField()
    network = serializers.ChoiceField(
        choices=['ethereum', 'sepolia', 'polygon'],
        default='sepolia'
    )

    def validate_wallet_address(self, value):
        from src.shared.validators import validate_wallet_address
        try:
            validate_wallet_address(value)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return value

class TokenResponseSerializer(serializers.Serializer):
    """Token response serializer"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = ProfileSerializer()
    expires_in = serializers.IntegerField()
