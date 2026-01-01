from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from rest_framework import status

import pytest

from gardeniq.base.utils.tests import ViewSetTestMixin


User = get_user_model()


@pytest.mark.django_db
class UserViewSetTestConf(ViewSetTestMixin):
    """Base configuration for User ViewSet tests."""
    BASE_PATTERN = "users"
    MODEL = User
    DATA_TO_DEFAULT_OBJ = {
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "password": "testpass123",
    }

    def generate_default_obj(self) -> User: # type: ignore
        """Generate a default user object for testing."""
        user = User.objects.create_user(
            username=self.DATA_TO_DEFAULT_OBJ["username"],
            first_name=self.DATA_TO_DEFAULT_OBJ["first_name"],
            last_name=self.DATA_TO_DEFAULT_OBJ["last_name"],
            email=self.DATA_TO_DEFAULT_OBJ["email"],
            password=self.DATA_TO_DEFAULT_OBJ["password"],
        )
        return user


@pytest.mark.django_db
class TestUserAPIModelViewList(UserViewSetTestConf):
    """Tests for listing users."""

    def test_list_users(self, client_anonymous, obj):
        """Test retrieving the list of users."""
        # GIVEN
        user = obj  # User created via fixture
        # Create additional user
        User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass456",
        )
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 2

        # Check response data format
        first_user = response.data["results"][0]
        assert "id" in first_user
        assert "username" in first_user
        assert "first_name" in first_user
        assert "last_name" in first_user
        assert "email" in first_user
        assert "is_staff" in first_user
        assert "is_active" in first_user
        assert "last_login" in first_user
        assert "date_joined" in first_user
        assert "groups" in first_user
        assert "user_permissions" in first_user
        # Password should not be in response
        assert "password" not in first_user

    def test_list_users_empty(self, client_anonymous):
        """Test listing users when no users exist."""
        # GIVEN
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_users_with_groups_and_permissions(self, client_anonymous, obj):
        """Test listing users with groups and permissions."""
        # GIVEN
        user = obj

        # Create group and permission
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename="test_permission",
            name="Test Permission",
            content_type=content_type,
        )
        group = Group.objects.create(name="Test Group")
        group.permissions.add(permission)

        # Add group and permission to user
        user.groups.add(group)
        user.user_permissions.add(permission)

        url = self.get_url_list()

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        user_data = next(u for u in response.data["results"] if u["id"] == user.id)
        assert len(user_data["groups"]) == 1
        assert user_data["groups"][0]["name"] == "Test Group"
        assert len(user_data["user_permissions"]) == 1
        assert user_data["user_permissions"][0]["codename"] == "test_permission"


@pytest.mark.django_db
class TestUserAPIModelViewRetrieve(UserViewSetTestConf):
    """Tests for retrieving a single user."""

    def test_retrieve_user(self, client_anonymous, obj):
        """Test retrieving a specific user."""
        # GIVEN
        user = obj
        url = self.get_url_detail(user.pk)

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == user.id
        assert response.data["username"] == user.username
        assert response.data["first_name"] == user.first_name
        assert response.data["last_name"] == user.last_name
        assert response.data["email"] == user.email
        assert response.data["is_staff"] == user.is_staff
        assert response.data["is_active"] == user.is_active
        assert "password" not in response.data

    def test_retrieve_nonexistent_user(self, client_anonymous):
        """Test retrieving a user that doesn't exist."""
        # GIVEN
        url = self.get_url_detail(99999)

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_user_with_groups(self, client_anonymous, obj):
        """Test retrieving a user with groups and permissions."""
        # GIVEN
        user = obj
        group = Group.objects.create(name="Developers")
        user.groups.add(group)

        url = self.get_url_detail(user.pk)

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["groups"]) == 1
        assert response.data["groups"][0]["name"] == "Developers"


@pytest.mark.django_db
class TestUserAPIModelViewCreate(UserViewSetTestConf):
    """Tests for creating users."""

    def test_create_user_minimal(self, client_anonymous):
        """Test creating a user with minimal required fields."""
        # GIVEN
        valid_payload = {
            "username": "newuser",
            "password": "newpass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, valid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == valid_payload["username"]
        assert "password" not in response.data

        # Check if the user was actually created in the database
        user = User.objects.get(username=valid_payload["username"])
        assert user is not None
        assert user.check_password(valid_payload["password"])

    def test_create_user_complete(self, client_anonymous):
        """Test creating a user with all fields."""
        # GIVEN
        valid_payload = {
            "username": "completeuser",
            "first_name": "Complete",
            "last_name": "User",
            "email": "complete@example.com",
            "password": "completepass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, valid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == valid_payload["username"]
        assert response.data["first_name"] == valid_payload["first_name"]
        assert response.data["last_name"] == valid_payload["last_name"]
        assert response.data["email"] == valid_payload["email"]

        # Check if the user was actually created in the database
        user = User.objects.get(username=valid_payload["username"])
        assert user.first_name == valid_payload["first_name"]
        assert user.last_name == valid_payload["last_name"]
        assert user.email == valid_payload["email"]
        assert user.check_password(valid_payload["password"])

    def test_create_user_with_groups(self, client_anonymous):
        """Test creating a user with groups."""
        # GIVEN
        group1 = Group.objects.create(name="Group1")
        group2 = Group.objects.create(name="Group2")

        valid_payload = {
            "username": "groupuser",
            "password": "grouppass123",
            "group_ids": [group1.pk, group2.pk],
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, valid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED

        # Check if groups were assigned
        user = User.objects.get(username=valid_payload["username"])
        assert user.groups.count() == 2
        assert group1 in user.groups.all()
        assert group2 in user.groups.all()

    def test_create_user_with_permissions(self, client_anonymous):
        """Test creating a user with specific permissions."""
        # GIVEN
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename="test_create_permission",
            name="Test Create Permission",
            content_type=content_type,
        )

        valid_payload = {
            "username": "permuser",
            "password": "permpass123",
            "permission_ids": [permission.pk],
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, valid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED

        # Check if permissions were assigned
        user = User.objects.get(username=valid_payload["username"])
        assert user.user_permissions.count() == 1
        assert permission in user.user_permissions.all()

    def test_create_user_without_username(self, client_anonymous):
        """Test creating a user without username should fail."""
        # GIVEN
        invalid_payload = {
            "password": "testpass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, invalid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_create_user_without_password(self, client_anonymous):
        """Test creating a user without password should fail."""
        # GIVEN
        invalid_payload = {
            "username": "nopassuser",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, invalid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_create_user_with_short_password(self, client_anonymous):
        """Test creating a user with password too short."""
        # GIVEN
        invalid_payload = {
            "username": "shortpass",
            "password": "short",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, invalid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_create_user_duplicate_username(self, client_anonymous, obj):
        """Test creating a user with duplicate username should fail."""
        # GIVEN
        user = obj
        invalid_payload = {
            "username": user.username,
            "password": "testpass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, invalid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_create_user_duplicate_email(self, client_anonymous, obj):
        """Test creating a user with duplicate email should fail."""
        # GIVEN
        user = obj
        invalid_payload = {
            "username": "newuser",
            "email": user.email,
            "password": "testpass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, invalid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_create_user_invalid_email(self, client_anonymous):
        """Test creating a user with invalid email format."""
        # GIVEN
        invalid_payload = {
            "username": "invalidemail",
            "email": "not-an-email",
            "password": "testpass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, invalid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_create_user_blank_username(self, client_anonymous):
        """Test creating a user with blank username should fail."""
        # GIVEN
        invalid_payload = {
            "username": "",
            "password": "testpass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, invalid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data


@pytest.mark.django_db
class TestUserAPIModelViewUpdate(UserViewSetTestConf):
    """Tests for updating users."""

    def test_update_user_put(self, client_anonymous, obj):
        """Test updating a user with PUT (full update)."""
        # GIVEN
        user = obj
        url = self.get_url_detail(user.pk)
        update_data = {
            "username": "updateduser",
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == update_data["username"]
        assert response.data["first_name"] == update_data["first_name"]
        assert response.data["last_name"] == update_data["last_name"]
        assert response.data["email"] == update_data["email"]

        # Check if the user was actually updated in the database
        updated_user = User.objects.get(pk=user.pk)
        assert updated_user.username == update_data["username"]
        assert updated_user.first_name == update_data["first_name"]
        assert updated_user.last_name == update_data["last_name"]
        assert updated_user.email == update_data["email"]

    def test_update_user_patch(self, client_anonymous, obj):
        """Test partially updating a user with PATCH."""
        # GIVEN
        user = obj
        url = self.get_url_detail(user.pk)
        update_data = {
            "first_name": "Patched",
        }

        # WHEN
        response = client_anonymous.patch(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == update_data["first_name"]
        # Other fields should remain unchanged
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email

    def test_update_user_password(self, client_anonymous, obj):
        """Test updating a user's password."""
        # GIVEN
        user = obj
        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,
            "password": "newpassword123",
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK

        # Check if password was updated
        updated_user = User.objects.get(pk=user.pk)
        assert updated_user.check_password("newpassword123")

    def test_update_user_groups(self, client_anonymous, obj):
        """Test updating a user's groups."""
        # GIVEN
        user = obj
        group1 = Group.objects.create(name="NewGroup1")
        group2 = Group.objects.create(name="NewGroup2")

        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,
            "group_ids": [group1.pk, group2.pk],
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK

        # Check if groups were updated
        updated_user = User.objects.get(pk=user.pk)
        assert updated_user.groups.count() == 2
        assert group1 in updated_user.groups.all()
        assert group2 in updated_user.groups.all()

    def test_update_user_permissions(self, client_anonymous, obj):
        """Test updating a user's permissions."""
        # GIVEN
        user = obj
        content_type = ContentType.objects.get_for_model(User)
        permission1 = Permission.objects.create(
            codename="test_update_perm1",
            name="Test Update Permission 1",
            content_type=content_type,
        )
        permission2 = Permission.objects.create(
            codename="test_update_perm2",
            name="Test Update Permission 2",
            content_type=content_type,
        )

        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,
            "permission_ids": [permission1.pk, permission2.pk],
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK

        # Check if permissions were updated
        updated_user = User.objects.get(pk=user.pk)
        assert updated_user.user_permissions.count() == 2
        assert permission1 in updated_user.user_permissions.all()
        assert permission2 in updated_user.user_permissions.all()

    def test_update_user_duplicate_username(self, client_anonymous, obj):
        """Test updating a user with a username that already exists."""
        # GIVEN
        user = obj
        other_user = User.objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        url = self.get_url_detail(user.pk)
        update_data = {
            "username": other_user.username,
        }

        # WHEN
        response = client_anonymous.patch(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_update_user_duplicate_email(self, client_anonymous, obj):
        """Test updating a user with an email that already exists."""
        # GIVEN
        user = obj
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="testpass123",
        )

        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,
            "email": other_user.email,
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_update_nonexistent_user(self, client_anonymous):
        """Test updating a user that doesn't exist."""
        # GIVEN
        url = self.get_url_detail(99999)
        update_data = {
            "username": "nonexistent",
        }

        # WHEN
        response = client_anonymous.patch(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_user_clear_optional_fields(self, client_anonymous, obj):
        """Test clearing optional fields (email, first_name, last_name)."""
        # GIVEN
        user = obj
        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,
            "first_name": "",
            "last_name": "",
            "email": "",
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == ""
        assert response.data["last_name"] == ""
        assert response.data["email"] == ""


@pytest.mark.django_db
class TestUserAPIModelViewDelete(UserViewSetTestConf):
    """Tests for deleting users."""

    def test_delete_user(self, client_anonymous, obj):
        """Test deleting a user."""
        # GIVEN
        user = obj
        user_id = user.pk
        url = self.get_url_detail(user.pk)

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Check if the user was actually deleted from the database
        assert not User.objects.filter(pk=user_id).exists()

    def test_delete_nonexistent_user(self, client_anonymous):
        """Test deleting a user that doesn't exist."""
        # GIVEN
        url = self.get_url_detail(99999)

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_user_with_groups(self, client_anonymous, obj):
        """Test deleting a user that has groups assigned."""
        # GIVEN
        user = obj
        group = Group.objects.create(name="TestGroup")
        user.groups.add(group)
        user_id = user.pk

        url = self.get_url_detail(user.pk)

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=user_id).exists()
        # Group should still exist
        assert Group.objects.filter(pk=group.pk).exists()

    def test_delete_user_with_permissions(self, client_anonymous, obj):
        """Test deleting a user that has permissions assigned."""
        # GIVEN
        user = obj
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename="test_delete_permission",
            name="Test Delete Permission",
            content_type=content_type,
        )
        user.user_permissions.add(permission)
        user_id = user.pk

        url = self.get_url_detail(user.pk)

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=user_id).exists()
        # Permission should still exist
        assert Permission.objects.filter(pk=permission.pk).exists()


@pytest.mark.django_db
class TestUserAPIModelViewEdgeCases(UserViewSetTestConf):
    """Tests for edge cases and special scenarios."""

    def test_create_user_with_very_long_username(self, client_anonymous):
        """Test creating a user with a username at the maximum length."""
        # GIVEN
        # Django's User model has max_length=150 for username
        valid_payload = {
            "username": "a" * 150,
            "password": "testpass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, valid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_user_with_username_too_long(self, client_anonymous):
        """Test creating a user with a username exceeding maximum length."""
        # GIVEN
        invalid_payload = {
            "username": "a" * 151,
            "password": "testpass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, invalid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_update_user_without_changing_username(self, client_anonymous, obj):
        """Test updating a user without changing the username (should allow same username)."""
        # GIVEN
        user = obj
        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,  # Same username
            "first_name": "Changed",
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username

    def test_update_user_without_changing_email(self, client_anonymous, obj):
        """Test updating a user without changing the email (should allow same email)."""
        # GIVEN
        user = obj
        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,
            "email": user.email,  # Same email
            "first_name": "Changed",
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_list_users_pagination(self, client_anonymous):
        """Test listing users with pagination."""
        # GIVEN
        # Create multiple users
        for i in range(15):
            User.objects.create_user(
                username=f"user{i}",
                password="testpass123",
            )
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert "count" in response.data
        assert response.data["count"] == 15

    def test_retrieve_user_fields_readonly(self, client_anonymous, obj):
        """Test that read-only fields are present in retrieve."""
        # GIVEN
        user = obj
        url = self.get_url_detail(user.pk)

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        # Check read-only fields
        assert "is_staff" in response.data
        assert "is_active" in response.data
        assert "last_login" in response.data
        assert "date_joined" in response.data
        # These should be read-only, test by attempting to modify them
        assert response.data["is_staff"] == user.is_staff
        assert response.data["is_active"] == user.is_active

    def test_update_readonly_fields_ignored(self, client_anonymous, obj):
        """Test that attempting to update read-only fields is ignored."""
        # GIVEN
        user = obj
        original_is_staff = user.is_staff
        original_is_active = user.is_active

        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,
            "is_staff": not original_is_staff,  # Try to change read-only field
            "is_active": not original_is_active,  # Try to change read-only field
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK

        # Read-only fields should remain unchanged
        updated_user = User.objects.get(pk=user.pk)
        assert updated_user.is_staff == original_is_staff
        assert updated_user.is_active == original_is_active

    def test_create_user_with_empty_email(self, client_anonymous):
        """Test creating a user with empty email is allowed."""
        # GIVEN
        valid_payload = {
            "username": "noemailuser",
            "email": "",
            "password": "testpass123",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, valid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == ""

    def test_user_string_representation(self, obj):
        """Test the __str__ method of the user model."""
        # GIVEN
        user = obj

        # WHEN
        user_str = str(user)

        # THEN
        expected = f"{user.first_name} {user.last_name}".strip() or user.username
        assert user_str == expected

    def test_user_string_representation_without_name(self):
        """Test the __str__ method when first_name and last_name are empty."""
        # GIVEN
        user = User.objects.create_user(
            username="noname",
            password="testpass123",
        )

        # WHEN
        user_str = str(user)

        # THEN
        assert user_str == user.username

    def test_update_user_remove_groups(self, client_anonymous, obj):
        """Test removing all groups from a user."""
        # GIVEN
        user = obj
        group = Group.objects.create(name="TempGroup")
        user.groups.add(group)

        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,
            "group_ids": [],  # Empty list to remove all groups
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK

        # Check if groups were removed
        updated_user = User.objects.get(pk=user.pk)
        assert updated_user.groups.count() == 0

    def test_update_user_remove_permissions(self, client_anonymous, obj):
        """Test removing all permissions from a user."""
        # GIVEN
        user = obj
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename="temp_permission",
            name="Temp Permission",
            content_type=content_type,
        )
        user.user_permissions.add(permission)

        url = self.get_url_detail(user.pk)
        update_data = {
            "username": user.username,
            "permission_ids": [],  # Empty list to remove all permissions
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK

        # Check if permissions were removed
        updated_user = User.objects.get(pk=user.pk)
        assert updated_user.user_permissions.count() == 0
