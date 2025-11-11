from rest_framework import status

import pytest

from gardeniq.base.models import Status
from gardeniq.base.utils import ViewSetTestMixin


@pytest.mark.django_db
class StatusViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "status"
    MODEL = Status
    DATA_TO_DEFAULT_OBJ = {
        "name": "Test Status",
        "tag": "test-status",
        "color": "#FF5733",
        "description": "Test Status Description",
    }


@pytest.mark.django_db
class TestStatusAPIModelView(StatusViewSetTestConf):
    def test_list_status(self, client_anonymous, obj):
        """Test retrieving the list of status"""
        # GIVEN
        # Status created via fixture
        url = self.get_url_list()
        expected = self.DATA_TO_DEFAULT_OBJ

        # WHEN
        response = client_anonymous.get(url)
        res_data = response.data["results"][0]

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert res_data["name"] == expected["name"]
        assert res_data["tag"] == expected["tag"]
        assert res_data["color"] == expected["color"]
        assert res_data["description"] == expected["description"]

    def test_retrieve_status(self, client_anonymous, obj):
        """Test retrieving a specific status"""
        # GIVEN
        # Status created via fixture
        status_obj = obj
        url = self.get_url_detail(status_obj)
        expected = self.DATA_TO_DEFAULT_OBJ

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == expected["name"]
        assert response.data["tag"] == expected["tag"]
        assert response.data["color"] == expected["color"]
        assert response.data["description"] == expected["description"]

    def test_create_status(self, client_anonymous):
        """Test creating a new status"""
        # GIVEN
        status_data = {
            "name": "New Status",
            "tag": "new-status",
            "color": "#00FF00",
            "description": "A new status description",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, data=status_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Status"
        assert response.data["tag"] == "new-status"
        assert response.data["color"] == "#00FF00"
        assert response.data["description"] == "A new status description"

        # Database verification
        status_obj = Status.objects.get(tag="new-status")
        assert status_obj.name == "New Status"
        assert status_obj.color == "#00FF00"
        assert status_obj.description == "A new status description"

    def test_create_status_without_description(self, client_anonymous):
        """Test creating a status without description (optional field)"""
        # GIVEN
        status_data = {
            "name": "Status Without Description",
            "tag": "no-description",
            "color": "#0000FF",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, data=status_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Status Without Description"
        assert response.data["tag"] == "no-description"
        assert response.data["color"] == "#0000FF"
        assert response.data["description"] == ""

    def test_create_status_with_default_color(self, client_anonymous):
        """Test creating a status with default color"""
        # GIVEN
        status_data = {
            "name": "Status Default Color",
            "tag": "default-color",
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, data=status_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["color"] == Status.DEFAULT_COLOR

    def test_update_status(self, client_anonymous, obj):
        """Test updating an existing status"""
        # GIVEN
        status_obj = obj
        url = self.get_url_detail(status_obj)
        update_data = {
            "name": "Updated Status",
            "tag": "updated-status",
            "color": "#FF0000",
            "description": "Updated description",
        }

        # WHEN
        response = client_anonymous.put(url, update_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Status"
        assert response.data["tag"] == "updated-status"
        assert response.data["color"] == "#FF0000"
        assert response.data["description"] == "Updated description"

        # Database verification
        status_obj.refresh_from_db()
        assert status_obj.name == "Updated Status"
        assert status_obj.tag == "updated-status"
        assert status_obj.color == "#FF0000"
        assert status_obj.description == "Updated description"

    def test_partial_update_status(self, client_anonymous, obj):
        """Test partial update of a status"""
        # GIVEN
        status_obj = obj
        url = self.get_url_detail(status_obj)
        patch_data = {"name": "Partially Updated Status"}

        # WHEN
        response = client_anonymous.patch(url, patch_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Partially Updated Status"
        assert response.data["tag"] == "test-status"  # unchanged
        assert response.data["color"] == "#FF5733"  # unchanged

        # Database verification
        status_obj.refresh_from_db()
        assert status_obj.name == "Partially Updated Status"
        assert status_obj.tag == "test-status"
        assert status_obj.color == "#FF5733"

    def test_partial_update_color(self, client_anonymous, obj):
        """Test partial update of status color"""
        # GIVEN
        status_obj = obj
        url = self.get_url_detail(status_obj)
        patch_data = {"color": "#123456"}

        # WHEN
        response = client_anonymous.patch(url, patch_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["color"] == "#123456"
        assert response.data["name"] == "Test Status"  # unchanged

        # Database verification
        status_obj.refresh_from_db()
        assert status_obj.color == "#123456"

    def test_delete_status(self, client_anonymous, obj):
        """Test deleting a status"""
        # GIVEN
        status_obj = obj
        status_count_before = Status.objects.count()
        url = self.get_url_detail(status_obj)

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Status.objects.count() == status_count_before - 1
        with pytest.raises(Status.DoesNotExist):
            Status.objects.get(id=status_obj.id)

    def test_create_status_invalid_color_format(self, client_anonymous):
        """Test creating a status with an invalid color format"""
        # GIVEN
        status_data = {
            "name": "Invalid Color Status",
            "tag": "invalid-color",
            "color": "INVALID",  # invalid color format
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, status_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "color" in response.data

    def test_create_status_invalid_color_too_long(self, client_anonymous):
        """Test creating a status with a color that's too long"""
        # GIVEN
        status_data = {
            "name": "Invalid Color Status",
            "tag": "invalid-color-long",
            "color": "#FF5733AA",  # too long
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, status_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "color" in response.data

    def test_create_status_invalid_color_missing_hash(self, client_anonymous):
        """Test creating a status with a color missing the # symbol"""
        # GIVEN
        status_data = {
            "name": "Invalid Color Status",
            "tag": "invalid-color-no-hash",
            "color": "FF5733",  # missing `#`
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, status_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "color" in response.data

    def test_create_status_short_color_format(self, client_anonymous):
        """Test creating a status with a valid short color format (#RGB)"""
        # GIVEN
        status_data = {
            "name": "Short Color Status",
            "tag": "short-color",
            "color": "#F5A",  # valid 3-character format
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, status_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["color"] == "#F5A"

    def test_create_status_missing_name(self, client_anonymous):
        """Test creating a status without a required name field"""
        # GIVEN
        status_data = {
            "tag": "missing-name",
            "color": "#FF5733",
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, status_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    def test_create_status_missing_tag(self, client_anonymous):
        """Test creating a status without a required tag field"""
        # GIVEN
        status_data = {
            "name": "Missing Tag Status",
            "color": "#FF5733",
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, status_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "tag" in response.data

    def test_create_status_invalid_tag_format(self, client_anonymous):
        """Test creating a status with an invalid tag format (slug validation)"""
        # GIVEN
        status_data = {
            "name": "Invalid Tag Status",
            "tag": "invalid tag with spaces",  # spaces not allowed in slug
            "color": "#FF5733",
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, status_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "tag" in response.data

    def test_retrieve_nonexistent_status(self, client_anonymous):
        """Test retrieving a status that doesn't exist"""
        # GIVEN
        url = self.get_url_detail(99999)  # non-existent ID

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_nonexistent_status(self, client_anonymous):
        """Test updating a status that doesn't exist"""
        # GIVEN
        url = self.get_url_detail(99999)  # non-existent ID
        update_data = {
            "name": "Updated Status",
            "tag": "updated-status",
            "color": "#FF0000",
        }

        # WHEN
        response = client_anonymous.put(url, update_data)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_status(self, client_anonymous):
        """Test deleting a status that doesn't exist"""
        # GIVEN
        url = self.get_url_detail(99999)  # non-existent ID

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND
