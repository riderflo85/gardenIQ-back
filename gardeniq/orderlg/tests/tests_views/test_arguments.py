from rest_framework import status

import pytest

from gardeniq.base.utils import ViewSetTestMixin
from gardeniq.orderlg.models import Argument


@pytest.mark.django_db
class ArgumentsViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "arguments"
    MODEL = Argument
    DATA_TO_DEFAULT_OBJ = {
        "description": "Test Argument",
        "slug": "test-argument",
        "value_type": "int",
        "required": True,
        "is_option": False,
    }


@pytest.mark.django_db
class TestArgumentAPIModelView(ArgumentsViewSetTestConf):
    def test_list_arguments(self, client_anonymous, obj):
        """Test retrieving the list of arguments"""
        # GIVEN
        # Argument created via fixture
        url = self.get_url_list()
        excepted = self.DATA_TO_DEFAULT_OBJ

        # WHEN
        response = client_anonymous.get(url)
        res_data = response.data["results"][0]

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert res_data["slug"] == excepted["slug"]
        assert res_data["description"] == excepted["description"]
        assert res_data["value_type"] == excepted["value_type"]
        assert res_data["required"] is True
        assert res_data["is_option"] is False

    def test_retrieve_argument(self, client_anonymous, obj):
        """Test retrieving a specific argument"""
        # GIVEN
        # Argument created via fixture
        argument = obj
        url = self.get_url_detail(argument)
        excepted = self.DATA_TO_DEFAULT_OBJ

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == excepted["slug"]
        assert response.data["description"] == excepted["description"]
        assert response.data["value_type"] == excepted["value_type"]
        assert response.data["required"] is True
        assert response.data["is_option"] is False

    def test_create_argument(self, client_anonymous):
        """Test creating a new argument"""
        # GIVEN
        argument_data = {
            "description": "New Argument",
            "slug": "new-argument",
            "value_type": "str",
            "required": False,
            "is_option": True,
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, data=argument_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["slug"] == "new-argument"
        assert response.data["description"] == "New Argument"
        assert response.data["value_type"] == "str"
        assert response.data["required"] is False
        assert response.data["is_option"] is True

        # Database verification
        argument = Argument.objects.get(slug="new-argument")
        assert argument.description == "New Argument"
        assert argument.value_type == "str"
        assert argument.required is False
        assert argument.is_option is True

    def test_update_argument(self, client_anonymous, obj):
        """Test updating an existing argument"""
        # GIVEN
        argument = obj
        url = self.get_url_detail(argument)
        update_data = {
            "description": "Updated Argument",
            "slug": "updated-argument",
            "value_type": "float",
            "required": False,
            "is_option": True,
        }

        # WHEN
        response = client_anonymous.put(url, update_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == "updated-argument"
        assert response.data["description"] == "Updated Argument"
        assert response.data["value_type"] == "float"
        assert response.data["required"] is False
        assert response.data["is_option"] is True

        # Database verification
        argument.refresh_from_db()
        assert argument.slug == "updated-argument"
        assert argument.description == "Updated Argument"
        assert argument.value_type == "float"
        assert argument.required is False
        assert argument.is_option is True

    def test_partial_update_argument(self, client_anonymous, obj):
        """Test partial update of an argument"""
        # GIVEN
        argument = obj
        url = self.get_url_detail(argument)
        patch_data = {"description": "Partially Updated Argument"}

        # WHEN
        response = client_anonymous.patch(url, patch_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == "Partially Updated Argument"
        assert response.data["slug"] == "test-argument"  # unchanged
        assert response.data["value_type"] == "int"  # unchanged

        # Database verification
        argument.refresh_from_db()
        assert argument.description == "Partially Updated Argument"
        assert argument.slug == "test-argument"
        assert argument.value_type == "int"

    def test_delete_argument(self, client_anonymous, obj):
        """Test deleting an argument"""
        # GIVEN
        argument = obj
        argument_count_before = Argument.objects.count()
        url = self.get_url_detail(argument)

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Argument.objects.count() == argument_count_before - 1
        with pytest.raises(Argument.DoesNotExist):
            Argument.objects.get(id=argument.id)

    def test_create_argument_invalid_value_type(self, client_anonymous):
        """Test creating an argument with an invalid value type"""
        # GIVEN
        argument_data = {
            "description": "Invalid Argument",
            "slug": "invalid-argument",
            "value_type": "invalid_type",  # invalid type
            "required": True,
            "is_option": False,
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, argument_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "value_type" in response.data
