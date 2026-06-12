from typing import Dict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.test import RequestFactory

from rest_framework.reverse import reverse
from rest_framework.test import APIClient

import pytest

User = get_user_model()


class ViewSetTestMixin:
    """A mixin class providing utility methods and fixtures for testing Django REST Framework ViewSets.

    Attributes:
        BASE_PATTERN (str): The base pattern name used for URL reversing.
        MODEL (type[Model]): The Django model class associated with the ViewSet.
        DATA_TO_DEFAULT_OBJ (Dict): Default data used to create a model instance for testing.

    Fixtures:
        client_anonymous() -> APIClient:
            Returns an anonymous APIClient instance for testing.

        obj() -> type[Model]:
            Returns a default model instance for use in tests.
    """

    BASE_PATTERN: str = ""
    MODEL: type[Model]
    DATA_TO_DEFAULT_OBJ: Dict

    def _return_obj_id(self, obj: type[Model] | int) -> int:
        """
        Returns the primary key (ID) of a given object.

        If the input is an integer, it is assumed to be the primary key and returned as is.
        If the input is a Django model instance, its primary key (`pk` attribute) is returned.

        Args:
            obj (type[Model] | int): A Django model instance or an integer representing the primary key.

        Returns:
            int: The primary key of the object.
        """
        if isinstance(obj, int):
            pk = obj
        else:
            pk = obj.pk
        return pk

    def get_url_list(self):
        return reverse(f"{self.BASE_PATTERN}-list")

    def get_url_create(self):
        return self.get_url_list()

    def get_url_detail(self, obj: type[Model] | int):
        pk = self._return_obj_id(obj)
        return reverse(f"{self.BASE_PATTERN}-detail", kwargs={"pk": pk})

    def get_url_enable(self, obj: type[Model] | int):
        pk = self._return_obj_id(obj)
        return reverse(f"{self.BASE_PATTERN}-enable", kwargs={"pk": pk})

    def get_url_disable(self, obj: type[Model] | int):
        pk = self._return_obj_id(obj)
        return reverse(f"{self.BASE_PATTERN}-disable", kwargs={"pk", pk})

    def generate_default_obj(self) -> type[Model]:
        new_obj = self.MODEL.objects.create(**self.DATA_TO_DEFAULT_OBJ)
        return new_obj  # type: ignore

    @pytest.fixture
    def client_anonymous(self) -> APIClient:
        client = APIClient()
        client.force_authenticate(None)
        return client

    @pytest.fixture
    def obj(self) -> type[Model]:
        return self.generate_default_obj()

    @pytest.fixture
    def mock_request_factory(self):
        """
        Factory fixture to create mock Django request objects with authenticated users.

        Returns a callable that accepts a user and returns a mock request with that user.
        """

        def _create_request(user):
            """Create a mock request with the given user."""
            factory = RequestFactory()
            request = factory.get("/")
            request.user = user
            return request

        return _create_request

    @pytest.fixture
    def user_content_type(self):
        """Return the content type for User model."""
        return ContentType.objects.get_for_model(User)

    @pytest.fixture
    def test_permission(self, user_content_type):
        """Create a test permission."""
        return Permission.objects.create(
            codename="test_permission", name="Test Permission", content_type=user_content_type
        )

    @pytest.fixture
    def test_permission_2(self, user_content_type):
        """Create a second test permission."""
        return Permission.objects.create(
            codename="test_permission_2", name="Test Permission 2", content_type=user_content_type
        )

    @pytest.fixture
    def test_group(self, test_permission):
        """Create a test group with permissions."""
        group = Group.objects.create(name="Test Group")
        group.permissions.add(test_permission)
        return group

    @pytest.fixture
    def test_group_2(self, test_permission_2):
        """Create a second test group with permissions."""
        group = Group.objects.create(name="Test Group 2")
        group.permissions.add(test_permission_2)
        return group

    @pytest.fixture
    def regular_user(self):
        """Create a regular non-staff user."""
        return User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="RegularPass123!",
            first_name="Regular",
            last_name="User",
        )

    @pytest.fixture
    def admin_user(self):
        """Create an admin user with staff privileges."""
        return User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="AdminPass123!",
            first_name="Admin",
            last_name="User",
            is_staff=True,
            is_superuser=True,
        )

    @pytest.fixture
    def regular_user_with_groups(self, regular_user, test_group, test_permission):
        """Create a regular user with groups and permissions."""
        regular_user.groups.add(test_group)
        regular_user.user_permissions.add(test_permission)
        return regular_user

    @pytest.fixture
    def api_client(self):
        """Return a DRF API client."""
        return APIClient()

    @pytest.fixture
    def authenticated_client(self, api_client, regular_user):
        """Return an authenticated API client for a regular user."""
        api_client.force_authenticate(user=regular_user)
        return api_client

    @pytest.fixture
    def admin_client(self, api_client, admin_user):
        """Return an authenticated API client for an admin user."""
        api_client.force_authenticate(user=admin_user)
        return api_client

    @pytest.fixture
    def unauthenticated_client(self, api_client):
        """Return an unauthenticated API client."""
        api_client.force_authenticate(user=None)
        return api_client

    @pytest.fixture
    def user_payload(self):
        """Return a valid user creation payload."""
        return {
            "username": "newuser",
            "password": "NewUserPass123!",
            "password_confirm": "NewUserPass123!",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
        }
