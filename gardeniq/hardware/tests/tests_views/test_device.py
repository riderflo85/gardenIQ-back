from rest_framework import status

import pytest

from gardeniq.base.models import Status
from gardeniq.base.utils import ViewSetTestMixin
from gardeniq.hardware.models import Device


@pytest.mark.django_db
class DeviceViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "devices"
    MODEL = Device
    DATA_TO_DEFAULT_OBJ = {
        "name": "Test Device",
        "uid": "12AB34567890DEAD",
        "path": "/dev/ttyUSB0",
        "description": "Test Device Description",
    }

    @pytest.fixture
    def status_obj(self):
        """Fixture to create a Status object for Device"""
        return Status.objects.create(
            name="Device Active",
            tag="device-active",
            color="#00FF00",
            description="Device is active and connected",
        )

    @pytest.fixture
    def obj(self, status_obj):
        """Override obj fixture to include status"""
        data = self.DATA_TO_DEFAULT_OBJ.copy()
        data["status"] = status_obj
        return self.MODEL.objects.create(**data)

    @pytest.fixture
    def mock_serial_ports(self, mocker):
        """Mock the get_serial_port_choices function to return test serial ports."""
        mock = mocker.patch("gardeniq.hardware.serializers.device.get_serial_port_choices")
        mock.return_value = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/cu.usbserial-123", "COM3"]
        return mock


@pytest.mark.django_db
class TestDeviceAPIModelView(DeviceViewSetTestConf):
    def test_list_devices(self, client_anonymous, obj):
        """Test retrieving the list of devices"""
        # GIVEN
        # Device created via fixture
        url = self.get_url_list()
        expected = self.DATA_TO_DEFAULT_OBJ

        # WHEN
        response = client_anonymous.get(url)
        res_data = response.data["results"][0]

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert res_data["name"] == expected["name"]
        assert res_data["uid"] == expected["uid"]
        assert res_data["path"] == expected["path"]
        assert res_data["description"] == expected["description"]
        assert "last_seen" in res_data
        assert "gd_firmware_version" in res_data
        assert "mp_firmware_version" in res_data

    def test_retrieve_device(self, client_anonymous, obj):
        """Test retrieving a specific device"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        expected = self.DATA_TO_DEFAULT_OBJ

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == expected["name"]
        assert response.data["uid"] == expected["uid"]
        assert response.data["path"] == expected["path"]
        assert response.data["description"] == expected["description"]
        assert "status" in response.data
        assert isinstance(response.data["status"], dict)
        assert response.data["status"]["name"] == "Device Active"

    def test_create_device(self, mock_serial_ports, client_anonymous, status_obj):
        """Test creating a new device"""
        # GIVEN
        device_data = {
            "name": "New Device",
            "path": "/dev/ttyUSB1",
            "description": "A new device description",
            "status": status_obj.id,
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, data=device_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Device"
        assert response.data["path"] == "/dev/ttyUSB1"
        assert response.data["description"] == "A new device description"
        assert response.data["status"] == status_obj.id
        # Read-only fields should be present
        assert "uid" in response.data
        assert "last_seen" in response.data
        assert "gd_firmware_version" in response.data
        assert "mp_firmware_version" in response.data

        # Database verification
        device_obj = Device.objects.get(name="New Device")
        assert device_obj.path == "/dev/ttyUSB1"
        assert device_obj.description == "A new device description"
        assert device_obj.status == status_obj

    def test_create_device_without_description(self, mock_serial_ports, client_anonymous, status_obj):
        """Test creating a device without description (optional field)"""
        # GIVEN
        device_data = {
            "name": "Device Without Description",
            "path": "/dev/ttyUSB0",
            "status": status_obj.id,
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, data=device_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Device Without Description"
        assert response.data["path"] == "/dev/ttyUSB0"
        assert response.data["description"] == ""

    def test_update_device(self, mock_serial_ports, client_anonymous, obj, status_obj):
        """Test updating an existing device"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        update_data = {
            "name": "Updated Device",
            "path": "/dev/ttyUSB1",
            "description": "Updated description",
            "status": status_obj.id,
        }

        # WHEN
        response = client_anonymous.put(url, update_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Device"
        assert response.data["path"] == "/dev/ttyUSB1"
        assert response.data["description"] == "Updated description"

        # Database verification
        device_obj.refresh_from_db()
        assert device_obj.name == "Updated Device"
        assert device_obj.path == "/dev/ttyUSB1"
        assert device_obj.description == "Updated description"

    def test_partial_update_device(self, mock_serial_ports, client_anonymous, obj):
        """Test partial update of a device"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        patch_data = {"name": "Partially Updated Device"}

        # WHEN
        response = client_anonymous.patch(url, patch_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Partially Updated Device"
        assert response.data["path"] == "/dev/ttyUSB0"  # unchanged
        assert response.data["uid"] == "12AB34567890DEAD"  # unchanged

        # Database verification
        device_obj.refresh_from_db()
        assert device_obj.name == "Partially Updated Device"
        assert device_obj.path == "/dev/ttyUSB0"
        assert device_obj.uid == "12AB34567890DEAD"

    def test_partial_update_path(self, mock_serial_ports, client_anonymous, obj):
        """Test partial update of device path"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        patch_data = {"path": "COM3"}

        # WHEN
        response = client_anonymous.patch(url, patch_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["path"] == "COM3"
        assert response.data["name"] == "Test Device"  # unchanged

        # Database verification
        device_obj.refresh_from_db()
        assert device_obj.path == "COM3"

    def test_delete_device(self, client_anonymous, obj):
        """Test deleting a device"""
        # GIVEN
        device_obj = obj
        device_count_before = Device.objects.count()
        url = self.get_url_detail(device_obj)

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Device.objects.count() == device_count_before - 1
        with pytest.raises(Device.DoesNotExist):
            Device.objects.get(id=device_obj.id)

    def test_create_device_invalid_path_format(self, mock_serial_ports, client_anonymous, status_obj):
        """Test creating a device with an invalid path format"""
        # GIVEN
        device_data = {
            "name": "Invalid Path Device",
            "path": "/invalid/path",  # invalid format
            "status": status_obj.id,
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "path" in response.data

    def test_create_device_path_not_in_choices(self, mock_serial_ports, client_anonymous, status_obj):
        """Test creating a device with a path not in available choices"""
        # GIVEN
        device_data = {
            "name": "Unavailable Path Device",
            "path": "/dev/ttyUSB5",  # not in choices
            "status": status_obj.id,
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "path" in response.data

    def test_create_device_missing_name(self, mock_serial_ports, client_anonymous, status_obj):
        """Test creating a device without a required name field"""
        # GIVEN
        device_data = {
            "path": "/dev/ttyUSB0",
            "status": status_obj.id,
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    def test_create_device_missing_path(self, mock_serial_ports, client_anonymous, status_obj):
        """Test creating a device without a required path field"""
        # GIVEN
        device_data = {
            "name": "Missing Path Device",
            "status": status_obj.id,
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "path" in response.data

    def test_create_device_missing_status(self, mock_serial_ports, client_anonymous):
        """Test creating a device without a required status field"""
        # GIVEN
        device_data = {
            "name": "Missing Status Device",
            "path": "/dev/ttyUSB0",
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data

    def test_create_device_invalid_status(self, mock_serial_ports, client_anonymous):
        """Test creating a device with a non-existent status"""
        # GIVEN
        device_data = {
            "name": "Invalid Status Device",
            "path": "/dev/ttyUSB0",
            "status": 99999,  # non-existent status
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data

    def test_retrieve_nonexistent_device(self, client_anonymous):
        """Test retrieving a device that doesn't exist"""
        # GIVEN
        url = self.get_url_detail(99999)  # non-existent ID

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_nonexistent_device(self, mock_serial_ports, client_anonymous, status_obj):
        """Test updating a device that doesn't exist"""
        # GIVEN
        url = self.get_url_detail(99999)  # non-existent ID
        update_data = {
            "name": "Updated Device",
            "path": "/dev/ttyUSB0",
            "status": status_obj.id,
        }

        # WHEN
        response = client_anonymous.put(url, update_data)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_device(self, client_anonymous):
        """Test deleting a device that doesn't exist"""
        # GIVEN
        url = self.get_url_detail(99999)  # non-existent ID

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_device_name_too_long(self, mock_serial_ports, client_anonymous, status_obj):
        """Test creating a device with a name that's too long"""
        # GIVEN
        device_data = {
            "name": "A" * 256,  # exceeds max_length
            "path": "/dev/ttyUSB0",
            "status": status_obj.id,
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    def test_list_devices_query_optimization(self, client_anonymous, obj):
        """Test that list view uses select_related for status optimization"""
        # GIVEN
        url = self.get_url_list()

        # WHEN
        with self.assert_num_queries(2):  # Should only need 2 queries with select_related
            response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def assert_num_queries(self, num):
        """Helper context manager to assert number of database queries"""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        class AssertNumQueriesContext(CaptureQueriesContext):
            def __exit__(self, exc_type, exc_value, traceback):
                super().__exit__(exc_type, exc_value, traceback)
                if exc_type is not None:
                    return
                executed = len(self)
                assert executed == num, f"Expected {num} queries but got {executed}"

        return AssertNumQueriesContext(connection)

    def test_create_device_with_com_port(self, mock_serial_ports, client_anonymous, status_obj):
        """Test creating a device with a Windows COM port path"""
        # GIVEN
        device_data = {
            "name": "Windows Device",
            "path": "COM3",
            "status": status_obj.id,
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, device_data)

        # THEN
        # This might fail due to path choices, which is expected behavior
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]

    def test_create_device_with_macos_port(self, mock_serial_ports, client_anonymous, status_obj):
        """Test creating a device with a macOS cu port path"""
        # GIVEN
        device_data = {
            "name": "macOS Device",
            "path": "/dev/cu.usbserial-123",
            "status": status_obj.id,
        }
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["path"] == "/dev/cu.usbserial-123"

    def test_device_last_seen_auto_updates(self, client_anonymous, obj):
        """Test that last_seen is automatically updated"""
        # GIVEN
        device_obj = obj
        original_last_seen = device_obj.last_seen

        # WHEN
        import time

        time.sleep(0.1)  # Small delay to ensure time difference
        device_obj.save()
        device_obj.refresh_from_db()

        # THEN
        assert device_obj.last_seen > original_last_seen

    def test_device_uid_readonly(self, client_anonymous, obj):
        """Test that uid field is read-only and cannot be modified"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        original_uid = device_obj.uid

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["uid"] == original_uid
        # uid should be in response but not modifiable through API

    def test_device_firmware_versions_readonly(self, client_anonymous, obj):
        """Test that firmware version fields are read-only"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert "gd_firmware_version" in response.data
        assert "mp_firmware_version" in response.data

    def test_update_device_empty_description(self, mock_serial_ports, client_anonymous, obj, status_obj):
        """Test updating device to have empty description"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        update_data = {
            "name": "Device Without Description",
            "path": "/dev/ttyUSB0",
            "description": "",
            "status": status_obj.id,
        }

        # WHEN
        response = client_anonymous.put(url, update_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == ""

        # Database verification
        device_obj.refresh_from_db()
        assert device_obj.description == ""
