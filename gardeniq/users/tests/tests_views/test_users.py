"""
Tests for UserAPIModelView.

Tests cover all CRUD operations with proper permission checks.
Uses the GIVEN-WHEN-THEN pattern for clarity.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Return a DRF API client."""
    return APIClient()


@pytest.fixture
def user_content_type():
    """Return the content type for User model."""
    return ContentType.objects.get_for_model(User)


@pytest.fixture
def test_permission(user_content_type):
    """Create a test permission."""
    return Permission.objects.create(
        codename='test_permission',
        name='Test Permission',
        content_type=user_content_type
    )


@pytest.fixture
def test_permission_2(user_content_type):
    """Create a second test permission."""
    return Permission.objects.create(
        codename='test_permission_2',
        name='Test Permission 2',
        content_type=user_content_type
    )


@pytest.fixture
def test_group(test_permission):
    """Create a test group with permissions."""
    group = Group.objects.create(name='Test Group')
    group.permissions.add(test_permission)
    return group


@pytest.fixture
def test_group_2(test_permission_2):
    """Create a second test group with permissions."""
    group = Group.objects.create(name='Test Group 2')
    group.permissions.add(test_permission_2)
    return group


@pytest.fixture
def regular_user():
    """Create a regular non-staff user."""
    return User.objects.create_user(
        username='regularuser',
        email='regular@example.com',
        password='RegularPass123!',
        first_name='Regular',
        last_name='User'
    )


@pytest.fixture
def admin_user():
    """Create an admin user with staff privileges."""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='AdminPass123!',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def regular_user_with_groups(regular_user, test_group, test_permission):
    """Create a regular user with groups and permissions."""
    regular_user.groups.add(test_group)
    regular_user.user_permissions.add(test_permission)
    return regular_user


@pytest.fixture
def authenticated_client(api_client, regular_user):
    """Return an authenticated API client for a regular user."""
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an authenticated API client for an admin user."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def unauthenticated_client(api_client):
    """Return an unauthenticated API client."""
    api_client.force_authenticate(user=None)
    return api_client


@pytest.fixture
def user_payload():
    """Return a valid user creation payload."""
    return {
        'username': 'newuser',
        'password': 'NewUserPass123!',
        'password_confirm': 'NewUserPass123!',
        'email': 'newuser@example.com',
        'first_name': 'New',
        'last_name': 'User'
    }


@pytest.mark.django_db
class TestUserAPIModelViewList:
    """Tests for listing users (GET /api/users/)."""

    def test_list_users_as_admin(self, admin_client, regular_user, admin_user):
        """Test that admin can list all users."""
        # GIVEN
        # Two users exist (regular_user and admin_user from fixtures)
        url = reverse('users-list')

        # WHEN
        response = admin_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or isinstance(response.data, list)
        # Verify at least 2 users in the response
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 2

    def test_list_users_as_regular_user_forbidden(self, authenticated_client):
        """Test that regular user cannot list users."""
        # GIVEN
        # Regular authenticated user
        url = reverse('users-list')

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_as_anonymous_forbidden(self, unauthenticated_client):
        """Test that anonymous user cannot list users."""
        # GIVEN
        # Unauthenticated client
        url = reverse('users-list')

        # WHEN
        response = unauthenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserAPIModelViewRetrieve:
    """Tests for retrieving user details (GET /api/users/{id}/)."""

    def test_retrieve_own_user_as_regular_user(self, authenticated_client, regular_user):
        """Test that user can retrieve their own details."""
        # GIVEN
        # Authenticated regular user
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == regular_user.pk
        assert response.data['username'] == regular_user.username
        assert response.data['email'] == regular_user.email
        assert 'groups' in response.data
        assert 'user_permissions' in response.data

    def test_retrieve_other_user_as_regular_user_forbidden(
        self, authenticated_client, regular_user, admin_user
    ):
        """Test that regular user cannot retrieve another user's details."""
        # GIVEN
        # Authenticated regular user trying to access admin user
        url = reverse('users-detail', kwargs={'pk': admin_user.pk})

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_any_user_as_admin(self, admin_client, regular_user):
        """Test that admin can retrieve any user's details."""
        # GIVEN
        # Authenticated admin user
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})

        # WHEN
        response = admin_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == regular_user.pk
        assert response.data['username'] == regular_user.username

    def test_retrieve_user_as_anonymous_forbidden(self, unauthenticated_client, regular_user):
        """Test that anonymous user cannot retrieve user details."""
        # GIVEN
        # Unauthenticated client
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})

        # WHEN
        response = unauthenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_nonexistent_user(self, admin_client):
        """Test retrieving a non-existent user returns 404."""
        # GIVEN
        # Admin client and non-existent user ID
        url = reverse('users-detail', kwargs={'pk': 99999})

        # WHEN
        response = admin_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUserAPIModelViewCreate:
    """Tests for creating users (POST /api/users/)."""

    def test_create_user_as_admin(self, admin_client, user_payload):
        """Test that admin can create a new user."""
        # GIVEN
        # Admin client and valid user data
        url = reverse('users-list')
        initial_count = User.objects.count()

        # WHEN
        response = admin_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['username'] == user_payload['username']
        assert response.data['email'] == user_payload['email']
        assert 'password' not in response.data
        assert User.objects.count() == initial_count + 1

        # Verify user in database
        user = User.objects.get(username=user_payload['username'])
        assert user.check_password(user_payload['password'])
        assert user.email == user_payload['email']

    def test_create_user_with_groups_and_permissions_as_admin(
        self, admin_client, user_payload, test_group, test_permission
    ):
        """Test that admin can create user with groups and permissions."""
        # GIVEN
        # Admin client and user data with groups and permissions
        url = reverse('users-list')
        user_payload['group_ids'] = [test_group.id]
        user_payload['permission_ids'] = [test_permission.id]

        # WHEN
        response = admin_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(username=user_payload['username'])
        assert user.groups.filter(id=test_group.id).exists()
        assert user.user_permissions.filter(id=test_permission.id).exists()

    def test_create_user_as_regular_user_forbidden(self, authenticated_client, user_payload):
        """Test that regular user cannot create users."""
        # GIVEN
        # Regular authenticated user
        url = reverse('users-list')

        # WHEN
        response = authenticated_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_user_as_anonymous_forbidden(self, unauthenticated_client, user_payload):
        """Test that anonymous user cannot create users."""
        # GIVEN
        # Unauthenticated client
        url = reverse('users-list')

        # WHEN
        response = unauthenticated_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_user_without_password_fails(self, admin_client, user_payload):
        """Test that creating user without password fails."""
        # GIVEN
        # User data without password
        del user_payload['password']
        url = reverse('users-list')

        # WHEN
        response = admin_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_create_user_without_password_confirm_fails(self, admin_client, user_payload):
        """Test that creating user without password confirmation fails."""
        # GIVEN
        # User data without password_confirm
        del user_payload['password_confirm']
        url = reverse('users-list')

        # WHEN
        response = admin_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    def test_create_user_with_mismatched_passwords_fails(self, admin_client, user_payload):
        """Test that creating user with mismatched passwords fails."""
        # GIVEN
        # User data with mismatched passwords
        user_payload['password_confirm'] = 'DifferentPass123!'
        url = reverse('users-list')

        # WHEN
        response = admin_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    def test_create_user_with_duplicate_username_fails(
        self, admin_client, user_payload, regular_user
    ):
        """Test that creating user with duplicate username fails."""
        # GIVEN
        # User data with existing username
        user_payload['username'] = regular_user.username
        url = reverse('users-list')

        # WHEN
        response = admin_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data

    def test_create_user_with_duplicate_email_fails(
        self, admin_client, user_payload, regular_user
    ):
        """Test that creating user with duplicate email fails."""
        # GIVEN
        # User data with existing email
        user_payload['email'] = regular_user.email
        url = reverse('users-list')

        # WHEN
        response = admin_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_create_user_with_short_password_fails(self, admin_client, user_payload):
        """Test that creating user with short password fails."""
        # GIVEN
        # User data with short password
        user_payload['password'] = 'short'
        user_payload['password_confirm'] = 'short'
        url = reverse('users-list')

        # WHEN
        response = admin_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_create_user_with_invalid_email_fails(self, admin_client, user_payload):
        """Test that creating user with invalid email fails."""
        # GIVEN
        # User data with invalid email
        user_payload['email'] = 'invalid-email'
        url = reverse('users-list')

        # WHEN
        response = admin_client.post(url, data=user_payload, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data


@pytest.mark.django_db
class TestUserAPIModelViewUpdate:
    """Tests for updating users (PUT /api/users/{id}/)."""

    def test_update_own_user_as_regular_user(self, authenticated_client, regular_user):
        """Test that user can update their own profile."""
        # GIVEN
        # Authenticated regular user
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})
        update_data = {
            'username': regular_user.username,
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }

        # WHEN
        response = authenticated_client.put(url, data=update_data, format='json')

        # THEN
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.first_name == 'Updated'
        assert regular_user.last_name == 'Name'
        assert regular_user.email == 'updated@example.com'

    def test_update_own_password_as_regular_user(self, authenticated_client, regular_user):
        """Test that user can update their own password."""
        # GIVEN
        # Authenticated regular user
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})
        update_data = {
            'username': regular_user.username,
            'password': 'NewPassword123!',
            'password_confirm': 'NewPassword123!'
        }

        # WHEN
        response = authenticated_client.put(url, data=update_data, format='json')

        # THEN
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.check_password('NewPassword123!')

    def test_update_other_user_as_regular_user_forbidden(
        self, authenticated_client, regular_user, admin_user
    ):
        """Test that regular user cannot update another user."""
        # GIVEN
        # Regular user trying to update admin user
        url = reverse('users-detail', kwargs={'pk': admin_user.pk})
        update_data = {
            'username': admin_user.username,
            'first_name': 'Hacked'
        }

        # WHEN
        response = authenticated_client.put(url, data=update_data, format='json')

        # THEN
        assert response.status_code == status.HTTP_403_FORBIDDEN
        admin_user.refresh_from_db()
        assert admin_user.first_name != 'Hacked'

    def test_update_any_user_as_admin(self, admin_client, regular_user):
        """Test that admin can update any user."""
        # GIVEN
        # Admin client updating regular user
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})
        update_data = {
            'username': regular_user.username,
            'first_name': 'AdminUpdated',
            'is_active': False
        }

        # WHEN
        response = admin_client.put(url, data=update_data, format='json')

        # THEN
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.first_name == 'AdminUpdated'
        assert regular_user.is_active is False

    def test_update_user_with_groups_as_admin(
        self, admin_client, regular_user, test_group, test_group_2
    ):
        """Test that admin can update user's groups."""
        # GIVEN
        # Admin updating user's groups
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})
        update_data = {
            'username': regular_user.username,
            'group_ids': [test_group.id, test_group_2.id]
        }

        # WHEN
        response = admin_client.put(url, data=update_data, format='json')

        # THEN
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.groups.count() == 2
        assert regular_user.groups.filter(id=test_group.id).exists()
        assert regular_user.groups.filter(id=test_group_2.id).exists()

    def test_update_user_with_mismatched_passwords_fails(
        self, authenticated_client, regular_user
    ):
        """Test that updating user with mismatched passwords fails."""
        # GIVEN
        # User data with mismatched passwords
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})
        update_data = {
            'username': regular_user.username,
            'password': 'NewPassword123!',
            'password_confirm': 'DifferentPass123!'
        }

        # WHEN
        response = authenticated_client.put(url, data=update_data, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_user_to_duplicate_username_fails(
        self, admin_client, regular_user, admin_user
    ):
        """Test that updating to duplicate username fails."""
        # GIVEN
        # Trying to use existing username
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})
        update_data = {
            'username': admin_user.username,  # Already exists
        }

        # WHEN
        response = admin_client.put(url, data=update_data, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data


@pytest.mark.django_db
class TestUserAPIModelViewDelete:
    """Tests for deleting users (DELETE /api/users/{id}/)."""

    def test_delete_user_as_admin(self, admin_client, regular_user):
        """Test that admin can delete a user."""
        # GIVEN
        # Admin client and existing user
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})
        user_id = regular_user.pk

        # WHEN
        response = admin_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=user_id).exists()

    def test_delete_user_as_regular_user_forbidden(
        self, authenticated_client, regular_user
    ):
        """Test that regular user cannot delete themselves."""
        # GIVEN
        # Regular user trying to delete themselves
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert User.objects.filter(pk=regular_user.pk).exists()

    def test_delete_user_as_anonymous_forbidden(
        self, unauthenticated_client, regular_user
    ):
        """Test that anonymous user cannot delete users."""
        # GIVEN
        # Unauthenticated client
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})

        # WHEN
        response = unauthenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert User.objects.filter(pk=regular_user.pk).exists()

    def test_delete_nonexistent_user(self, admin_client):
        """Test deleting non-existent user returns 404."""
        # GIVEN
        # Admin client and non-existent user ID
        url = reverse('users-detail', kwargs={'pk': 99999})

        # WHEN
        response = admin_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestUserAPIModelViewPermissions:
    """Tests for permission edge cases and special scenarios."""

    def test_regular_user_cannot_assign_groups(
        self, authenticated_client, regular_user, test_group
    ):
        """Test that regular user cannot assign groups to themselves."""
        # GIVEN
        # Regular user trying to add groups
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})
        update_data = {
            'username': regular_user.username,
            'group_ids': [test_group.id]
        }

        # WHEN
        response = authenticated_client.put(url, data=update_data, format='json')

        # THEN
        # The validation should fail at serializer level
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'group_ids' in response.data

    def test_regular_user_cannot_assign_permissions(
        self, authenticated_client, regular_user, test_permission
    ):
        """Test that regular user cannot assign permissions to themselves."""
        # GIVEN
        # Regular user trying to add permissions
        url = reverse('users-detail', kwargs={'pk': regular_user.pk})
        update_data = {
            'username': regular_user.username,
            'permission_ids': [test_permission.id]
        }

        # WHEN
        response = authenticated_client.put(url, data=update_data, format='json')

        # THEN
        # The validation should fail at serializer level
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'permission_ids' in response.data
