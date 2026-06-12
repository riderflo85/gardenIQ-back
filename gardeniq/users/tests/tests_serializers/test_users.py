"""
Tests for User serializers.

Tests cover UserSerializer and UserReadOnlySerializer with all validation scenarios.
Uses pytest and the GIVEN-WHEN-THEN pattern for clarity.
"""

from django.contrib.auth import get_user_model

import pytest

from gardeniq.base.utils.tests import ViewSetTestMixin
from gardeniq.users.serializers.users import UserDetailReadOnlySerializer
from gardeniq.users.serializers.users import UserReadOnlySerializer
from gardeniq.users.serializers.users import UserSerializer

User = get_user_model()


@pytest.mark.django_db
class TestUserSerializerCreate(ViewSetTestMixin):
    """Tests for creating users with UserSerializer."""

    def test_create_user_with_required_fields(self, mock_request_factory, admin_user):
        """Test creating a user with only required fields."""
        # GIVEN
        # Valid user data with minimum requirements
        data = {"username": "newuser", "password": "NewPass123!", "password_confirm": "NewPass123!"}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors
        user = serializer.save()
        assert user.username == "newuser"
        assert user.check_password("NewPass123!")

    def test_create_user_with_all_fields(
        self, mock_request_factory, admin_user, test_group, test_group_2, test_permission, test_permission_2
    ):
        """Test creating a user with all fields."""
        # GIVEN
        # Complete user data
        data = {
            "username": "fulluser",
            "password": "FullPass123!",
            "password_confirm": "FullPass123!",
            "email": "fulluser@example.com",
            "first_name": "Full",
            "last_name": "User",
            "group_ids": [test_group.id, test_group_2.id],
            "permission_ids": [test_permission.id, test_permission_2.id],
        }
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors
        user = serializer.save()
        assert user.username == "fulluser"
        assert user.email == "fulluser@example.com"
        assert user.first_name == "Full"
        assert user.last_name == "User"
        assert user.check_password("FullPass123!")
        assert user.groups.count() == 2
        assert test_group in user.groups.all()
        assert test_group_2 in user.groups.all()
        assert user.user_permissions.count() == 2

    def test_create_user_without_password_fails(self, mock_request_factory, admin_user):
        """Test that creating user without password fails."""
        # GIVEN
        # User data missing password
        data = {"username": "nopassuser"}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "password" in serializer.errors

    def test_create_user_without_password_confirm_fails(self, mock_request_factory, admin_user):
        """Test that creating user without password confirmation fails."""
        # GIVEN
        # User data missing password_confirm
        data = {"username": "noconfirmuser", "password": "TestPass123!"}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "password_confirm" in serializer.errors

    def test_create_user_without_username_fails(self, mock_request_factory, admin_user):
        """Test that creating user without username fails."""
        # GIVEN
        # User data missing username
        data = {"password": "TestPass123!", "password_confirm": "TestPass123!"}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "username" in serializer.errors

    def test_create_user_with_mismatched_passwords_fails(self, mock_request_factory, admin_user):
        """Test that creating user with mismatched passwords fails."""
        # GIVEN
        # Passwords don't match
        data = {"username": "mismatchuser", "password": "Password123!", "password_confirm": "DifferentPass123!"}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "password_confirm" in serializer.errors

    def test_create_user_with_short_password_fails(self, mock_request_factory, admin_user):
        """Test that creating user with short password fails."""
        # GIVEN
        # Password too short
        data = {"username": "shortpass", "password": "short", "password_confirm": "short"}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "password" in serializer.errors

    def test_create_user_with_blank_username_fails(self, mock_request_factory, admin_user):
        """Test that creating user with blank username fails."""
        # GIVEN
        # Blank username
        data = {"username": "", "password": "TestPass123!", "password_confirm": "TestPass123!"}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "username" in serializer.errors

    def test_create_user_with_duplicate_username_fails(self, mock_request_factory, admin_user, regular_user):
        """Test that creating user with duplicate username fails."""
        # GIVEN
        # Username already exists
        data = {"username": regular_user.username, "password": "TestPass123!", "password_confirm": "TestPass123!"}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "username" in serializer.errors

    def test_create_user_with_duplicate_email_fails(self, mock_request_factory, admin_user, regular_user):
        """Test that creating user with duplicate email fails."""
        # GIVEN
        # Email already exists
        data = {
            "username": "newuser",
            "email": regular_user.email,
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
        }
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "email" in serializer.errors

    def test_create_user_with_empty_email_succeeds(self, mock_request_factory, admin_user):
        """Test that creating user with empty email is allowed."""
        # GIVEN
        # Empty email (optional field)
        data = {"username": "noemail", "password": "TestPass123!", "password_confirm": "TestPass123!", "email": ""}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors
        user = serializer.save()
        assert user.email == ""

    def test_create_user_with_invalid_email_fails(self, mock_request_factory, admin_user):
        """Test that creating user with invalid email fails."""
        # GIVEN
        # Invalid email format
        data = {
            "username": "bademail",
            "email": "not-an-email",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
        }
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(data=data, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "email" in serializer.errors


@pytest.mark.django_db
class TestUserSerializerUpdate(ViewSetTestMixin):
    """Tests for updating users with UserSerializer."""

    def test_update_user_basic_fields(self, mock_request_factory, regular_user):
        """Test updating user basic fields."""
        # GIVEN
        # Existing user and update data
        data = {"first_name": "Updated", "last_name": "Name", "email": "updated@example.com"}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors
        user = serializer.save()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"
        assert user.email == "updated@example.com"

    def test_update_user_password(self, mock_request_factory, regular_user):
        """Test updating user password."""
        # GIVEN
        # User and new password
        old_password_hash = regular_user.password
        data = {"password": "NewPassword123!", "password_confirm": "NewPassword123!"}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors
        user = serializer.save()
        assert user.password != old_password_hash
        assert user.check_password("NewPassword123!")

    def test_update_user_username(self, mock_request_factory, regular_user):
        """Test updating user username."""
        # GIVEN
        # New username
        data = {"username": "updatedusername"}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors
        user = serializer.save()
        assert user.username == "updatedusername"

    def test_update_user_with_duplicate_username_fails(self, mock_request_factory, regular_user, admin_user):
        """Test that updating to duplicate username fails."""
        # GIVEN
        # Trying to use another user's username
        data = {"username": admin_user.username}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "username" in serializer.errors

    def test_update_user_with_duplicate_email_fails(self, mock_request_factory, regular_user, admin_user):
        """Test that updating to duplicate email fails."""
        # GIVEN
        # Trying to use another user's email
        data = {"email": admin_user.email}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "email" in serializer.errors

    def test_update_user_with_same_username_succeeds(self, mock_request_factory, regular_user):
        """Test that updating with same username succeeds."""
        # GIVEN
        # Same username, different field
        data = {"username": regular_user.username, "first_name": "Updated"}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors

    def test_update_user_with_same_email_succeeds(self, mock_request_factory, regular_user):
        """Test that updating with same email succeeds."""
        # GIVEN
        # Same email, different field
        data = {"email": regular_user.email, "first_name": "Updated"}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors

    def test_update_user_groups_as_admin(
        self, mock_request_factory, admin_user, regular_user, test_group, test_group_2
    ):
        """Test that admin can update user groups."""
        # GIVEN
        # Admin updating groups
        data = {"group_ids": [test_group.id, test_group_2.id]}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors
        user = serializer.save()
        assert user.groups.count() == 2
        assert test_group in user.groups.all()
        assert test_group_2 in user.groups.all()

    def test_update_user_permissions_as_admin(self, mock_request_factory, admin_user, regular_user, test_permission):
        """Test that admin can update user permissions."""
        # GIVEN
        # Admin updating permissions
        data = {"permission_ids": [test_permission.id]}
        mock_request = mock_request_factory(admin_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors
        user = serializer.save()
        assert user.user_permissions.count() == 1
        assert test_permission in user.user_permissions.all()

    def test_update_without_password_succeeds(self, mock_request_factory, regular_user):
        """Test that password is not required for update."""
        # GIVEN
        # Update without password
        data = {"first_name": "Updated"}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert is_valid, serializer.errors

    def test_update_password_with_mismatched_confirm_fails(self, mock_request_factory, regular_user):
        """Test that updating password with mismatched confirmation fails."""
        # GIVEN
        # Mismatched passwords
        data = {"password": "NewPassword123!", "password_confirm": "DifferentPass123!"}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "password_confirm" in serializer.errors


@pytest.mark.django_db
class TestUserSerializerValidation(ViewSetTestMixin):
    """Tests for UserSerializer validation and field constraints."""

    def test_group_ids_validation_non_admin_fails(self, mock_request_factory, regular_user, test_group):
        """Test that non-admin cannot assign groups."""
        # GIVEN
        # Regular user trying to assign groups
        data = {"group_ids": [test_group.id]}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "group_ids" in serializer.errors

    def test_permission_ids_validation_non_admin_fails(self, mock_request_factory, regular_user, test_permission):
        """Test that non-admin cannot assign permissions."""
        # GIVEN
        # Regular user trying to assign permissions
        data = {"permission_ids": [test_permission.id]}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()

        # THEN
        assert not is_valid
        assert "permission_ids" in serializer.errors

    def test_serializer_representation_excludes_password(self, mock_request_factory, regular_user):
        """Test that password is not in serialized output."""
        # GIVEN
        # Serializer instance
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, context={"request": mock_request})

        # WHEN
        data = serializer.data

        # THEN
        assert "password" not in data
        assert data["id"] == regular_user.id
        assert data["username"] == regular_user.username

    def test_is_staff_field_is_readonly(self, mock_request_factory, regular_user):
        """Test that is_staff field is read-only."""
        # GIVEN
        # Trying to set is_staff
        data = {"is_staff": True}
        mock_request = mock_request_factory(regular_user)
        serializer = UserSerializer(instance=regular_user, data=data, partial=True, context={"request": mock_request})

        # WHEN
        is_valid = serializer.is_valid()
        user = serializer.save()

        # THEN
        assert is_valid
        # is_staff should not have changed
        assert user.is_staff is False


@pytest.mark.django_db
class TestUserReadOnlySerializer(ViewSetTestMixin):
    """Tests for UserReadOnlySerializer."""

    def test_readonly_serializer_representation(self, regular_user_with_groups, test_group, test_permission):
        """Test that read-only serializer includes all expected fields."""
        # GIVEN
        # User with groups and permissions
        serializer = UserDetailReadOnlySerializer(instance=regular_user_with_groups)

        # WHEN
        data = serializer.data

        # THEN
        assert data["id"] == regular_user_with_groups.id
        assert data["username"] == regular_user_with_groups.username
        assert data["email"] == regular_user_with_groups.email
        assert "groups" in data
        assert len(data["groups"]) > 0
        assert any(g["name"] == test_group.name for g in data["groups"])
        assert "user_permissions" in data
        assert len(data["user_permissions"]) > 0

    def test_readonly_serializer_all_fields_readonly(self, regular_user):
        """Test that all fields in read-only serializer are read-only."""
        # GIVEN
        # Read-only serializer
        serializer = UserReadOnlySerializer(instance=regular_user)

        # WHEN
        # Check all fields

        # THEN
        for field_name, field in serializer.fields.items():
            assert field.read_only, f"Field '{field_name}' should be read-only"

    def test_readonly_serializer_cannot_create(self):
        """Test that read-only serializer cannot create objects."""
        # GIVEN
        # Data for creation
        data = {"username": "newuser", "password": "NewPass123!"}
        serializer = UserReadOnlySerializer(data=data)

        # WHEN/THEN
        # Should raise NotImplementedError when trying to save
        with pytest.raises(NotImplementedError):
            serializer.save()

    def test_readonly_serializer_with_multiple_groups(self, regular_user, test_group, test_group_2):
        """Test read-only serializer with multiple groups."""
        # GIVEN
        # User with multiple groups
        regular_user.groups.add(test_group, test_group_2)
        serializer = UserDetailReadOnlySerializer(instance=regular_user)

        # WHEN
        data = serializer.data

        # THEN
        assert len(data["groups"]) == 2
        group_names = [g["name"] for g in data["groups"]]
        assert test_group.name in group_names
        assert test_group_2.name in group_names

    def test_readonly_serializer_with_no_groups_or_permissions(self, regular_user):
        """Test read-only serializer with user having no groups or permissions."""
        # GIVEN
        # User without groups or permissions
        regular_user.groups.clear()
        regular_user.user_permissions.clear()
        serializer = UserDetailReadOnlySerializer(instance=regular_user)

        # WHEN
        data = serializer.data

        # THEN
        assert len(data["groups"]) == 0
        assert len(data["user_permissions"]) == 0

    def test_readonly_serializer_many(self, regular_user, admin_user):
        """Test read-only serializer with many=True."""
        # GIVEN
        # Multiple users
        users = User.objects.filter(id__in=[regular_user.id, admin_user.id])
        serializer = UserReadOnlySerializer(users, many=True)

        # WHEN
        data = serializer.data

        # THEN
        assert len(data) == 2
        usernames = [u["username"] for u in data]
        assert regular_user.username in usernames
        assert admin_user.username in usernames
