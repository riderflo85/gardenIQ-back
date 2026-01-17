"""
Tests for authentication views (LoginView and UserAuthViewSet).

Tests cover login functionality, throttling, and user profile retrieval.
Uses the GIVEN-WHEN-THEN pattern for clarity.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from unittest.mock import patch

User = get_user_model()


@pytest.fixture(autouse=True)
def disable_throttling():
    """
    Disable throttling for all tests by default.

    This fixture automatically disables DRF throttling to prevent test failures
    due to rate limiting. Individual tests can re-enable throttling if needed
    to test throttle-specific behavior.
    """
    with patch('gardeniq.users.views.auth.LoginThrottle.allow_request', return_value=True):
        yield


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
class TestLoginView:
    """Tests for user login (POST /api/auth/login/)."""

    def test_login_with_valid_credentials(self, api_client, regular_user):
        """Test successful login with valid credentials."""
        # GIVEN
        # Regular user with known credentials
        url = reverse('knox_login')
        credentials = {
            'username': 'regularuser',
            'password': 'RegularPass123!'
        }

        # WHEN
        response = api_client.post(url, data=credentials, format='json')

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert 'expiry' in response.data
        assert isinstance(response.data['token'], str)
        assert len(response.data['token']) > 0

    def test_login_with_invalid_username(self, api_client):
        """Test login with non-existent username fails."""
        # GIVEN
        # Non-existent username
        url = reverse('knox_login')
        credentials = {
            'username': 'nonexistent',
            'password': 'SomePassword123!'
        }

        # WHEN
        response = api_client.post(url, data=credentials, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_with_invalid_password(self, api_client, regular_user):
        """Test login with incorrect password fails."""
        # GIVEN
        # Existing user with wrong password
        url = reverse('knox_login')
        credentials = {
            'username': 'regularuser',
            'password': 'WrongPassword123!'
        }

        # WHEN
        response = api_client.post(url, data=credentials, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_with_missing_username(self, api_client):
        """Test login without username fails."""
        # GIVEN
        # Credentials missing username
        url = reverse('knox_login')
        credentials = {
            'password': 'SomePassword123!'
        }

        # WHEN
        response = api_client.post(url, data=credentials, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data

    def test_login_with_missing_password(self, api_client):
        """Test login without password fails."""
        # GIVEN
        # Credentials missing password
        url = reverse('knox_login')
        credentials = {
            'username': 'regularuser'
        }

        # WHEN
        response = api_client.post(url, data=credentials, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_login_with_empty_credentials(self, api_client):
        """Test login with empty credentials fails."""
        # GIVEN
        # Empty credentials
        url = reverse('knox_login')
        credentials = {}

        # WHEN
        response = api_client.post(url, data=credentials, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data
        assert 'password' in response.data

    def test_login_with_inactive_user(self, api_client, regular_user):
        """Test login with inactive user fails."""
        # GIVEN
        # User marked as inactive
        regular_user.is_active = False
        regular_user.save()
        url = reverse('knox_login')
        credentials = {
            'username': 'regularuser',
            'password': 'RegularPass123!'
        }

        # WHEN
        response = api_client.post(url, data=credentials, format='json')

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_throttling_triggered(self, api_client, regular_user):
        """Test that login is throttled after too many attempts."""
        # GIVEN
        # Mock the throttle check method to simulate throttling
        from unittest.mock import MagicMock
        from gardeniq.users.views.auth import LoginView

        # Create a mock that returns False (throttled)
        mock_throttle = MagicMock()
        mock_throttle.allow_request.return_value = False

        url = reverse('knox_login')
        credentials = {
            'username': 'regularuser',
            'password': 'WrongPassword123!'
        }

        # WHEN
        # Patch the throttle classes directly on the view
        with patch.object(LoginView, 'throttle_classes', [type('MockThrottle', (), {
            'allow_request': lambda self, request, view: False,
            'wait': lambda self: 60
        })]):
            response = api_client.post(url, data=credentials, format='json')

        # THEN
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_login_creates_auth_token(self, api_client, regular_user):
        """Test that successful login creates an authentication token."""
        # GIVEN
        # Regular user and valid credentials
        url = reverse('knox_login')
        credentials = {
            'username': 'regularuser',
            'password': 'RegularPass123!'
        }

        # WHEN
        response = api_client.post(url, data=credentials, format='json')
        token = response.data['token']

        # THEN
        assert response.status_code == status.HTTP_200_OK
        # Verify token can be used for authentication
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        me_url = reverse('auth-me')
        me_response = api_client.get(me_url)
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.data['username'] == 'regularuser'

    def test_multiple_logins_create_multiple_tokens(self, api_client, regular_user):
        """Test that multiple logins create separate tokens."""
        # GIVEN
        # Regular user logging in multiple times
        url = reverse('knox_login')
        credentials = {
            'username': 'regularuser',
            'password': 'RegularPass123!'
        }

        # WHEN
        response1 = api_client.post(url, data=credentials, format='json')
        response2 = api_client.post(url, data=credentials, format='json')

        # THEN
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        # Tokens should be different
        assert response1.data['token'] != response2.data['token']


@pytest.mark.django_db
class TestUserAuthViewSet:
    """Tests for UserAuthViewSet (/api/auth/me/)."""

    def test_get_authenticated_user_profile(self, authenticated_client, regular_user):
        """Test retrieving authenticated user's profile."""
        # GIVEN
        # Authenticated user
        url = reverse('auth-me')

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == regular_user.pk
        assert response.data['username'] == regular_user.username
        assert response.data['email'] == regular_user.email
        assert response.data['first_name'] == regular_user.first_name
        assert response.data['last_name'] == regular_user.last_name
        assert 'groups' in response.data
        assert 'user_permissions' in response.data
        assert 'password' not in response.data

    def test_get_admin_user_profile(self, admin_client, admin_user):
        """Test retrieving admin user's profile."""
        # GIVEN
        # Authenticated admin user
        url = reverse('auth-me')

        # WHEN
        response = admin_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == admin_user.pk
        assert response.data['username'] == admin_user.username
        assert response.data['is_staff'] is True

    def test_get_user_profile_includes_groups(
        self, authenticated_client, regular_user_with_groups, test_group
    ):
        """Test that user profile includes groups."""
        # GIVEN
        # Authenticated user with groups
        url = reverse('auth-me')

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert 'groups' in response.data
        assert len(response.data['groups']) > 0
        assert any(g['name'] == test_group.name for g in response.data['groups'])

    def test_get_user_profile_includes_permissions(
        self, authenticated_client, regular_user_with_groups, test_permission
    ):
        """Test that user profile includes permissions."""
        # GIVEN
        # Authenticated user with permissions
        url = reverse('auth-me')

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert 'user_permissions' in response.data
        assert len(response.data['user_permissions']) > 0
        assert any(
            p['codename'] == test_permission.codename
            for p in response.data['user_permissions']
        )

    def test_get_user_profile_unauthenticated_fails(self, unauthenticated_client):
        """Test that unauthenticated user cannot access /me endpoint."""
        # GIVEN
        # Unauthenticated client
        url = reverse('auth-me')

        # WHEN
        response = unauthenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_endpoint_is_read_only(self, authenticated_client, regular_user):
        """Test that /me endpoint does not support POST/PUT/DELETE."""
        # GIVEN
        # Authenticated user
        url = reverse('auth-me')
        data = {'username': 'hacked'}

        # WHEN
        post_response = authenticated_client.post(url, data=data, format='json')
        put_response = authenticated_client.put(url, data=data, format='json')
        delete_response = authenticated_client.delete(url)

        # THEN
        assert post_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert put_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert delete_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestLogoutView:
    """Tests for logout functionality."""

    def test_logout_authenticated_user(self, api_client, regular_user):
        """Test logging out an authenticated user."""
        # GIVEN
        # User logs in first
        login_url = reverse('knox_login')
        credentials = {
            'username': 'regularuser',
            'password': 'RegularPass123!'
        }
        login_response = api_client.post(login_url, data=credentials, format='json')
        token = login_response.data['token']

        # User is authenticated with token
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        logout_url = reverse('knox_logout')

        # WHEN
        response = api_client.post(logout_url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify token is no longer valid
        me_url = reverse('auth-me')
        me_response = api_client.get(me_url)
        assert me_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_unauthenticated_fails(self, unauthenticated_client):
        """Test that logout without authentication fails."""
        # GIVEN
        # Unauthenticated client
        url = reverse('knox_logout')

        # WHEN
        response = unauthenticated_client.post(url)

        # THEN
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogoutAllView:
    """Tests for logging out all sessions."""

    def test_logoutall_invalidates_all_tokens(self, api_client, regular_user):
        """Test that logoutall invalidates all user tokens."""
        # GIVEN
        # User logs in multiple times
        login_url = reverse('knox_login')
        credentials = {
            'username': 'regularuser',
            'password': 'RegularPass123!'
        }

        login1 = api_client.post(login_url, data=credentials, format='json')
        login2 = api_client.post(login_url, data=credentials, format='json')
        token1 = login1.data['token']
        token2 = login2.data['token']

        # Use token1 for logoutall
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token1}')
        logoutall_url = reverse('knox_logoutall')

        # WHEN
        response = api_client.post(logoutall_url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify both tokens are invalid
        me_url = reverse('auth-me')

        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token1}')
        me1_response = api_client.get(me_url)
        assert me1_response.status_code == status.HTTP_401_UNAUTHORIZED

        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token2}')
        me2_response = api_client.get(me_url)
        assert me2_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logoutall_unauthenticated_fails(self, unauthenticated_client):
        """Test that logoutall without authentication fails."""
        # GIVEN
        # Unauthenticated client
        url = reverse('knox_logoutall')

        # WHEN
        response = unauthenticated_client.post(url)

        # THEN
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
