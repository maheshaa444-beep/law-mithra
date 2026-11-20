from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    id = serializers.IntegerField(source='user.id', read_only=True)
    full_name = serializers.CharField(source='user.first_name', read_only=True)
    is_staff = serializers.BooleanField(source='user.is_staff', read_only=True)
    is_superuser = serializers.BooleanField(source='user.is_superuser', read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'email', 'full_name', 'is_staff', 'is_superuser', 'preferred_language', 'text_size', 'created_at', 'updated_at')
        read_only_fields = ('id', 'email', 'full_name', 'is_staff', 'is_superuser', 'created_at', 'updated_at')


class UserRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, allow_blank=True, default='', max_length=150)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    preferred_language = serializers.ChoiceField(
        choices=UserProfile.Language.choices,
        default=UserProfile.Language.ENGLISH,
        required=False
    )
    text_size = serializers.ChoiceField(
        choices=UserProfile.TextSize.choices,
        default=UserProfile.TextSize.NORMAL,
        required=False
    )

    def validate_full_name(self, value):
        name = value.strip()
        if value and len(name) < 2:
            raise serializers.ValidationError("Full name must be at least 2 characters long.")
        return name

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(
            models.Q(email__iexact=normalized_email) | models.Q(username__iexact=normalized_email)
        ).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return normalized_email

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if confirm_password and password != confirm_password:
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})

        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        full_name = validated_data.get('full_name', '').strip()
        preferred_language = validated_data.get('preferred_language', UserProfile.Language.ENGLISH)
        text_size = validated_data.get('text_size', UserProfile.TextSize.NORMAL)

        # Split full_name into first_name and last_name if space exists
        parts = full_name.split(' ', 1)
        first_name = full_name  # Keep complete full name in first_name for single-field display
        last_name = parts[1] if len(parts) > 1 else ''

        # Use email address as the username (case-insensitive, stored lowercase)
        user = User(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        user.set_password(password)
        user.save()

        # Update profile preferences
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.preferred_language = preferred_language
        profile.text_size = text_size
        profile.save()

        user.refresh_from_db()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True, max_length=254)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        raw_credential = attrs.get('email', '').strip()
        normalized_credential = raw_credential.lower()
        password = attrs.get('password', '')

        # Query users matching by normalized email, normalized username, or raw credential
        candidates = list(
            User.objects.filter(
                models.Q(email__iexact=normalized_credential) |
                models.Q(username__iexact=normalized_credential) |
                models.Q(username__iexact=raw_credential)
            ).order_by('id')
        )

        if not candidates:
            raise serializers.ValidationError("Invalid email or password.")

        authenticated_user = None
        for candidate in candidates:
            if candidate.check_password(password):
                authenticated_user = candidate
                break

        if not authenticated_user:
            raise serializers.ValidationError("Invalid email or password.")

        if not authenticated_user.is_active:
            raise serializers.ValidationError("Account is disabled.")

        attrs['user'] = authenticated_user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        user = self.context.get('request').user if self.context.get('request') else None
        validate_password(value, user)
        return value

    def validate(self, attrs):
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        if current_password and new_password and current_password == new_password:
            raise serializers.ValidationError(
                {"new_password": ["New password must be different from current password."]}
            )
        return attrs


class AccountDeletionSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, write_only=True)

    def validate_password(self, value):
        user = self.context.get('request').user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password. Account deletion requires valid password confirmation.")
        return value
