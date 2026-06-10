from typing import Dict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password as password_validation
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import ReadOnlySerializer

from .groups import GroupReadOnlySerializer
from .permissions import PermissionReadOnlySerializer

User = get_user_model()


class UserSerializer(BaseSerializer):
    """
    Serializer for creating a new basic user.
    """

    class Meta:
        model = User

    # id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150)

    # Password is required on creation but optional on update
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    password_confirm = serializers.CharField(write_only=True, min_length=8, required=False)

    first_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)
    email = serializers.EmailField(
        allow_blank=True,
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all(), message="A user with this email already exists.")],
    )

    is_staff = serializers.BooleanField(default=False, read_only=True)
    is_active = serializers.BooleanField(default=True)

    group_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Group.objects.all(), source="groups", write_only=True, required=False
    )
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), source="user_permissions", write_only=True, required=False
    )

    def _check_user_is_staff(self, error_msg: str):
        if not self.context["request"].user.is_staff:
            raise serializers.ValidationError(error_msg)

    def validate_group_ids(self, value):
        self._check_user_is_staff("Only administrators can assign groups.")
        return value

    def validate_permission_ids(self, value):
        self._check_user_is_staff("Only administrators can assign permissions.")
        return value

    def validate_username(self, value: str) -> str:
        """
        Validate username uniqueness.
        """
        user_qs = User.objects.filter(username=value)
        # Allow user to keep their own username during update
        if self.instance:
            user_qs = user_qs.exclude(pk=self.instance.pk)

        if user_qs.exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_password(self, value: str) -> str:
        try:
            password_validation(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """
        Validate that passwords match.
        """
        # Only require password and username on creation, not update
        is_creation = not self.instance

        # If password is provided, password_confirm must also be provided and match
        if "password" in attrs:
            if "password_confirm" not in attrs:
                raise serializers.ValidationError({"password_confirm": "The password confirmation is required."})
            if attrs["password"] != attrs["password_confirm"]:
                raise serializers.ValidationError({"password_confirm": "The passwords do not match."})

        # Password is required at creation
        if is_creation and "password" not in attrs:
            raise serializers.ValidationError({"password": "The password is required at creation."})

        # Remove password_confirm as it should not be saved
        attrs.pop("password_confirm", None)

        return attrs

    def create(self, validated_data: Dict):
        """
        Create a new user with hashed password.
        """
        groups = validated_data.pop("groups", [])
        user_permissions = validated_data.pop("user_permissions", [])
        password = validated_data.pop("password", None)

        user: User = super().create(validated_data)  # type: ignore
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
        password = validated_data.pop("password", None)
        groups = validated_data.pop("groups", None)
        user_permissions = validated_data.pop("user_permissions", None)

        if password:
            instance.set_password(password)

        instance = super().update(instance, validated_data)

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

    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)


class UserDetailReadOnlySerializer(UserReadOnlySerializer):
    """
    Detailed read-only serializer for User instances, including groups and permissions.
    """

    groups = GroupReadOnlySerializer(many=True, read_only=True)
    user_permissions = PermissionReadOnlySerializer(many=True, read_only=True)
