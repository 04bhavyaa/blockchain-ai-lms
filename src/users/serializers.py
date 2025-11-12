"""
User service serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'education_level', 'learning_goals'
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'avatar_url', 'bio', 'education_level',
            'learning_goals', 'token_balance', 'wallet_address',
            'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'token_balance', 'is_verified', 'created_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Update profile serializer"""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'avatar_url', 'bio',
            'education_level', 'learning_goals'
        ]


class ConnectWalletSerializer(serializers.Serializer):
    """Connect Web3 wallet serializer"""
    wallet_address = serializers.CharField(max_length=42, min_length=42)
    
    def validate_wallet_address(self, value):
        if not value.startswith('0x'):
            raise serializers.ValidationError("Invalid wallet address format")
        if User.objects.filter(wallet_address=value).exists():
            raise serializers.ValidationError("Wallet already connected to another account")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return data
