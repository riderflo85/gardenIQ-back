from typing import Dict

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from gardeniq.base.serializers import ReadOnlySerializer
from .permissions import PermissionSerializer
from .groups import GroupSerializer

User = get_user_model()

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150, required=True, allow_blank=False)
    first_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    email = serializers.EmailField(allow_blank=True, required=False)
    password = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=False)
    is_staff = serializers.BooleanField(default=False, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)

    group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        source='groups',
        write_only=True,
        required=False
    )
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        source='user_permissions',
        write_only=True,
        required=False
    )

    def validate(self, attrs):
        if not self.instance:
            if 'password' not in attrs:
                raise serializers.ValidationError({
                    "password": "The password is required at creation."
                })
            if 'username' not in attrs:
                raise serializers.ValidationError({
                    "username": "The username is required at creation."
                })
        return attrs

    def validate_username(self, value: str) -> str:
        """
        Validate username uniqueness.
        """
        user_qs = User.objects.filter(username=value)
        # if update, ignore the current user
        if self.instance:
            user_qs = user_qs.exclude(pk=self.instance.pk)
        if user_qs.exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def validate_email(self, value: str) -> str:
        """
        Validate email uniqueness if provided.
        """
        if value:  # Only if email is provided
            user_qs = User.objects.filter(email=value)
            if self.instance:
                user_qs = user_qs.exclude(pk=self.instance.pk)
            if user_qs.exists():
                raise serializers.ValidationError(
                    "A user with this email already exists."
                )
        return value

    def create(self, validated_data: Dict):
        """
        Create a new user with hashed password.
        """
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', [])
        user_permissions = validated_data.pop('user_permissions', [])

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Set groups and permissions
        if groups:
            user.groups.set(groups)
        if user_permissions:
            user.user_permissions.set(user_permissions)

        return user

    def update(self, instance, validated_data: Dict):
        """
        Update user, handling password separately.
        """
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', None)
        user_permissions = validated_data.pop('user_permissions', None)

        if password:
            instance.set_password(password)

        for key, value in validated_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.save()

        # Update groups and permissions if provided
        if groups is not None:
            instance.groups.set(groups)
        if user_permissions is not None:
            instance.user_permissions.set(user_permissions)

        return instance

class UserReadOnlySerializer(ReadOnlySerializer, UserSerializer):
    """
    Read-only serializer for User instances.

    Improves performance by avoiding validation and modification processing.
    Use for GET requests and nested representations.
    """
    groups = GroupSerializer(many=True, read_only=True)
    user_permissions = PermissionSerializer(many=True, read_only=True)

