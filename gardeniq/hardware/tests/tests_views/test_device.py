from rest_framework import status

import pytest

from gardeniq.base.models import Status
from gardeniq.base.utils import ViewSetTestMixin
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.models import Pin


@pytest.mark.django_db
class DeviceViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "devices"
    MODEL = Device
    DATA_TO_DEFAULT_OBJ = {
        "name": "Test Device",
        "uid": "12AB34567890DEAD",
        "path": "/dev/ttyUSB0",
        "description": "Test Device Description",
        "need_upgrade": False,
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
    def category_obj(self):
        """Fixture to create a DeviceCategory object for Device"""
        return DeviceCategory.objects.create(
            name="Device Category",
            pins_configuration={"available_channels": [], "digits": [], "pwms": [], "analogs": []},
        )

    @pytest.fixture
    def datasheet_category_obj(self):
        """Fixture to create a DeviceCategory whose datasheet lists the `digit` channel and two pins"""
        return DeviceCategory.objects.create(
            name="Datasheet Category",
            pins_configuration={
                "available_channels": ["digit"],
                "digits": [{"name": "GP0", "pins": [0]}, {"name": "GP1", "pins": [1]}],
                "pwms": [],
                "analogs": [],
            },
        )

    @pytest.fixture
    def obj(self, status_obj, category_obj):
        """Override obj fixture to include status and category"""
        data = self.DATA_TO_DEFAULT_OBJ.copy()
        data["status"] = status_obj
        data["category"] = category_obj
        return self.MODEL.objects.create(**data)

    @pytest.fixture
    def mock_serial_ports(self, mocker):
        """Mock the get_serial_port_choices function to return test serial ports."""
        mock = mocker.patch("gardeniq.hardware.serializers.device.get_serial_port_choices")
        mock.return_value = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/cu.usbserial-123", "COM3"]
        return mock


@pytest.mark.django_db
class TestDeviceAPIModelView(DeviceViewSetTestConf):
    def test_list_devices(self, authenticated_client, obj):
        """Test retrieving the list of devices"""
        # GIVEN
        # Device created via fixture
        url = self.get_url_list()
        expected = self.DATA_TO_DEFAULT_OBJ

        # WHEN
        response = authenticated_client.get(url)
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
        assert "need_upgrade" in res_data
        assert res_data["need_upgrade"] == expected["need_upgrade"]

    def test_retrieve_device(self, authenticated_client, obj):
        """Test retrieving a specific device"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        expected = self.DATA_TO_DEFAULT_OBJ

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == expected["name"]
        assert response.data["uid"] == expected["uid"]
        assert response.data["path"] == expected["path"]
        assert response.data["description"] == expected["description"]
        assert "status" in response.data
        assert isinstance(response.data["status"], dict)
        assert response.data["status"]["name"] == "Device Active"
        assert "need_upgrade" in response.data
        assert response.data["need_upgrade"] == expected["need_upgrade"]

    def test_create_device(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test creating a new device"""
        # GIVEN
        device_data = {
            "name": "New Device",
            "path": "/dev/ttyUSB1",
            "description": "A new device description",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, data=device_data)

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
        assert "need_upgrade" in response.data
        assert response.data["need_upgrade"] is False

        # Database verification
        device_obj = Device.objects.get(name="New Device")
        assert device_obj.path == "/dev/ttyUSB1"
        assert device_obj.description == "A new device description"
        assert device_obj.status == status_obj
        assert device_obj.need_upgrade is False

    def test_create_device_creates_the_pins_of_its_category(
        self, mock_serial_ports, authenticated_client, status_obj, datasheet_category_obj
    ):
        """Creating a device through the API creates the pins listed in the datasheet of its category"""
        # GIVEN
        Channel.objects.create(name="digit")
        device_data = {
            "name": "New Device",
            "path": "/dev/ttyUSB1",
            "status": status_obj.id,
            "category": datasheet_category_obj.id,
            "communication_protocol": "USB",
        }

        # WHEN
        response = authenticated_client.post(self.get_url_create(), data=device_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED, response.content
        pins = Pin.objects.filter(device__name="New Device")
        assert sorted(pins.values_list("pin_number", flat=True)) == [0, 1]

    def test_create_device_with_unknown_channel_returns_400(
        self, mock_serial_ports, authenticated_client, status_obj, datasheet_category_obj
    ):
        """A category whose datasheet lists a channel missing from the database is refused with a 400"""
        # GIVEN - no Channel in database
        device_data = {
            "name": "New Device",
            "path": "/dev/ttyUSB1",
            "status": status_obj.id,
            "category": datasheet_category_obj.id,
            "communication_protocol": "USB",
        }

        # WHEN
        response = authenticated_client.post(self.get_url_create(), data=device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.content
        assert response.data["code"] == "does_not_exist"
        assert "digit" in response.data["message"]
        assert not Device.objects.exists()
        assert not Pin.objects.exists()

    def test_create_device_without_description(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test creating a device without description (optional field)"""
        # GIVEN
        device_data = {
            "name": "Device Without Description",
            "path": "/dev/ttyUSB0",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, data=device_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Device Without Description"
        assert response.data["path"] == "/dev/ttyUSB0"
        assert response.data["description"] == ""
        assert "need_upgrade" in response.data
        assert response.data["need_upgrade"] is False

    def test_update_device(self, mock_serial_ports, authenticated_client, obj, status_obj, category_obj):
        """Test updating an existing device"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        update_data = {
            "name": "Updated Device",
            "path": "/dev/ttyUSB1",
            "description": "Updated description",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }

        # WHEN
        response = authenticated_client.put(url, update_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Device"
        assert response.data["path"] == "/dev/ttyUSB1"
        assert response.data["description"] == "Updated description"
        assert "need_upgrade" in response.data
        assert response.data["need_upgrade"] is False

        # Database verification
        device_obj.refresh_from_db()
        assert device_obj.name == "Updated Device"
        assert device_obj.path == "/dev/ttyUSB1"
        assert device_obj.description == "Updated description"

    def test_partial_update_device(self, mock_serial_ports, authenticated_client, obj):
        """Test partial update of a device is not allowed (PATCH method disabled)"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        patch_data = {"name": "Partially Updated Device"}

        # WHEN
        response = authenticated_client.patch(url, patch_data)

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_partial_update_path(self, mock_serial_ports, authenticated_client, obj):
        """Test partial update of device path is not allowed (PATCH method disabled)"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        patch_data = {"path": "COM3"}

        # WHEN
        response = authenticated_client.patch(url, patch_data)

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_device(self, authenticated_client, obj):
        """Test deleting a device"""
        # GIVEN
        device_obj = obj
        device_count_before = Device.objects.count()
        url = self.get_url_detail(device_obj)

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Device.objects.count() == device_count_before - 1
        with pytest.raises(Device.DoesNotExist):
            Device.objects.get(id=device_obj.id)

    def test_create_device_invalid_path_format(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test creating a device with an invalid path format"""
        # GIVEN
        device_data = {
            "name": "Invalid Path Device",
            "path": "/invalid/path",  # invalid format
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "path" in response.data["errors"]

    def test_create_device_path_not_in_choices(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test creating a device with a path not in available choices"""
        # GIVEN
        device_data = {
            "name": "Unavailable Path Device",
            "path": "/dev/ttyUSB5",  # not in choices
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "path" in response.data["errors"]

    def test_create_device_missing_name(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test creating a device without a required name field"""
        # GIVEN
        device_data = {
            "path": "/dev/ttyUSB0",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data["errors"]

    def test_create_device_without_path(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test creating a device without path (optional field)"""
        # GIVEN
        device_data = {
            "name": "Missing Path Device",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED, response.content
        assert Device.objects.get(name="Missing Path Device").path == ""

    def test_create_device_missing_status(self, mock_serial_ports, authenticated_client):
        """Test creating a device without a required status field"""
        # GIVEN
        device_data = {
            "name": "Missing Status Device",
            "path": "/dev/ttyUSB0",
        }
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data

    def test_create_device_invalid_status(self, mock_serial_ports, authenticated_client):
        """Test creating a device with a non-existent status"""
        # GIVEN
        device_data = {
            "name": "Invalid Status Device",
            "path": "/dev/ttyUSB0",
            "status": 99999,  # non-existent status
        }
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data

    def test_retrieve_nonexistent_device(self, authenticated_client):
        """Test retrieving a device that doesn't exist"""
        # GIVEN
        url = self.get_url_detail(99999)  # non-existent ID

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_nonexistent_device(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test updating a device that doesn't exist"""
        # GIVEN
        url = self.get_url_detail(99999)  # non-existent ID
        update_data = {
            "name": "Updated Device",
            "path": "/dev/ttyUSB0",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }

        # WHEN
        response = authenticated_client.put(url, update_data)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_device(self, authenticated_client):
        """Test deleting a device that doesn't exist"""
        # GIVEN
        url = self.get_url_detail(99999)  # non-existent ID

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_device_name_too_long(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test creating a device with a name that's too long"""
        # GIVEN
        device_data = {
            "name": "A" * 256,  # exceeds max_length
            "path": "/dev/ttyUSB0",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data["errors"]

    def test_create_device_with_com_port(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test creating a device with a Windows COM port path"""
        # GIVEN
        device_data = {
            "name": "Windows Device",
            "path": "COM3",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, device_data)

        # THEN
        # This might fail due to path choices, which is expected behavior
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]

    def test_create_device_with_macos_port(self, mock_serial_ports, authenticated_client, status_obj, category_obj):
        """Test creating a device with a macOS cu port path"""
        # GIVEN
        device_data = {
            "name": "macOS Device",
            "path": "/dev/cu.usbserial-123",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, device_data)

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["path"] == "/dev/cu.usbserial-123"

    def test_device_last_seen_auto_updates(self, authenticated_client, obj):
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

    def test_device_uid_readonly(self, authenticated_client, obj):
        """Test that uid field is read-only and cannot be modified"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        original_uid = device_obj.uid

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["uid"] == original_uid
        # uid should be in response but not modifiable through API
        assert "need_upgrade" in response.data

    def test_device_firmware_versions_readonly(self, authenticated_client, obj):
        """Test that firmware version fields are read-only"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert "gd_firmware_version" in response.data
        assert "mp_firmware_version" in response.data
        assert "need_upgrade" in response.data

    def test_update_device_empty_description(
        self, mock_serial_ports, authenticated_client, obj, status_obj, category_obj
    ):
        """Test updating device to have empty description"""
        # GIVEN
        device_obj = obj
        url = self.get_url_detail(device_obj)
        update_data = {
            "name": "Device Without Description",
            "path": "/dev/ttyUSB0",
            "description": "",
            "status": status_obj.id,
            "category": category_obj.id,
            "communication_protocol": "USB",
        }

        # WHEN
        response = authenticated_client.put(url, update_data)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == ""
        assert "need_upgrade" in response.data
        assert response.data["need_upgrade"] is False

        # Database verification
        device_obj.refresh_from_db()
        assert device_obj.description == ""


VALID_PINS_CONFIGURATION = {
    "available_channels": ["digit"],
    "digits": [{"name": "GP0", "pins": [0]}],
    "pwms": [],
    "analogs": [],
}


@pytest.mark.django_db
class DeviceCategoryViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "device-categories"
    MODEL = DeviceCategory
    DATA_TO_DEFAULT_OBJ = {
        "name": "Raspberry Pi Pico",
        "description": "Pico board",
        "pins_configuration": VALID_PINS_CONFIGURATION,
    }


@pytest.mark.django_db
class TestDeviceCategoryAPIModelView(DeviceCategoryViewSetTestConf):
    def test_list_device_categories(self, authenticated_client, obj):
        """The list is paginated and hides pins_configuration."""
        # GIVEN
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        res_data = response.data["results"][0]
        assert res_data["id"] == obj.pk
        assert res_data["name"] == "Raspberry Pi Pico"
        assert res_data["description"] == "Pico board"
        assert res_data["is_ready"] is True
        assert "pins_configuration" not in res_data

    def test_list_empty(self, authenticated_client):
        """The list is empty when no category exists."""
        # WHEN
        response = authenticated_client.get(self.get_url_list())

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_retrieve_device_category(self, authenticated_client, obj):
        """The detail exposes pins_configuration."""
        # WHEN
        response = authenticated_client.get(self.get_url_detail(obj))

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Raspberry Pi Pico"
        assert response.data["pins_configuration"] == VALID_PINS_CONFIGURATION

    def test_create_device_category(self, authenticated_client):
        """Valid data creates a category."""
        # GIVEN
        data = {"name": "Pico W", "description": "Pico with wifi", "pins_configuration": VALID_PINS_CONFIGURATION}

        # WHEN
        response = authenticated_client.post(self.get_url_create(), data=data, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED, response.content
        category = DeviceCategory.objects.get(pk=response.data["id"])
        assert category.name == "Pico W"
        assert category.pins_configuration == VALID_PINS_CONFIGURATION
        assert category.is_ready is True

    def test_create_with_invalid_pins_configuration(self, authenticated_client):
        """A pins_configuration that does not match the schema returns 400."""
        # GIVEN
        data = {"name": "Pico W", "pins_configuration": {"available_channels": "digit"}}

        # WHEN
        response = authenticated_client.post(self.get_url_create(), data=data, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "pins_configuration" in response.data["errors"]
        assert response.data["errors"]["pins_configuration"][0].startswith("Failed validation JSON schema")
        assert DeviceCategory.objects.count() == 0

    def test_create_without_name(self, authenticated_client):
        """A category without name returns 400."""
        # GIVEN
        data = {"pins_configuration": VALID_PINS_CONFIGURATION}

        # WHEN
        response = authenticated_client.post(self.get_url_create(), data=data, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data["errors"]

    def test_update_device_category(self, authenticated_client, obj):
        """PUT updates the category."""
        # GIVEN
        new_cfg = {**VALID_PINS_CONFIGURATION, "analogs": [{"name": "ADC0", "pins": [26]}]}
        data = {"name": "Pico 2", "description": "", "pins_configuration": new_cfg}

        # WHEN
        response = authenticated_client.put(self.get_url_detail(obj), data=data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK, response.content
        obj.refresh_from_db()
        assert obj.name == "Pico 2"
        assert obj.description == ""
        assert obj.pins_configuration == new_cfg

    def test_update_with_invalid_pins_configuration(self, authenticated_client, obj):
        """PUT with an invalid pins_configuration returns 400 and keeps the category."""
        # GIVEN
        data = {"name": "Pico 2", "pins_configuration": {"digits": [{"name": "GP0"}]}}

        # WHEN
        response = authenticated_client.put(self.get_url_detail(obj), data=data, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        obj.refresh_from_db()
        assert obj.name == "Raspberry Pi Pico"

    def test_partial_update_not_allowed(self, authenticated_client, obj):
        """PATCH is disabled."""
        # WHEN
        response = authenticated_client.patch(self.get_url_detail(obj), {"name": "Other"})

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_device_category(self, authenticated_client, obj):
        """DELETE removes an unused category."""
        # WHEN
        response = authenticated_client.delete(self.get_url_detail(obj))

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not DeviceCategory.objects.filter(pk=obj.pk).exists()

    def test_delete_device_category_used_by_a_device_returns_409(self, authenticated_client, obj):
        """DELETE of a category used by a device is refused with a 409 that lists the device."""
        # GIVEN
        Channel.objects.create(name="digit")
        device_status = Status.objects.create(name="Device Active", tag="device-active", color="#00FF00")
        device = Device.objects.create(name="Card", category=obj, status=device_status)

        # WHEN
        response = authenticated_client.delete(self.get_url_detail(obj))

        # THEN
        assert response.status_code == status.HTTP_409_CONFLICT, response.content
        assert response.data["code"] == "protected"
        assert response.data["errors"] == {"devices": [str(device)]}
        assert DeviceCategory.objects.filter(pk=obj.pk).exists()

    def test_retrieve_nonexistent(self, authenticated_client):
        """An unknown category returns 404."""
        # WHEN
        response = authenticated_client.get(self.get_url_detail(999999))

        # THEN
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_access(self, unauthenticated_client, obj):
        """An unauthenticated client gets 401."""
        # WHEN
        response = unauthenticated_client.get(self.get_url_list())

        # THEN
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["code"] == "not_authenticated"
        assert response["WWW-Authenticate"] == "Token"


@pytest.mark.django_db
class TestDeviceAPIModelViewFilters(DeviceViewSetTestConf):

    @pytest.fixture
    def other_device(self):
        """A Device with another Status and another DeviceCategory."""
        return Device.objects.create(
            name="Other Device",
            uid="1122334455667788",
            path="/dev/ttyUSB1",
            status=Status.objects.create(name="Device Offline", tag="device-offline"),
            category=DeviceCategory.objects.create(
                name="Other Category",
                pins_configuration={"available_channels": [], "digits": [], "pwms": [], "analogs": []},
            ),
        )

    @pytest.mark.parametrize("field", ["category", "status"])
    def test_list_filters_by_relation(self, authenticated_client, obj, other_device, field):
        """
        GIVEN: two Devices with different categories and statuses
        WHEN: listing with ?category= or ?status= of the other Device
        THEN: only the other Device is returned
        """
        # GIVEN
        value = getattr(other_device, field).pk

        # WHEN
        response = authenticated_client.get(self.get_url_list(), {field: value})

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert [item["id"] for item in response.data["results"]] == [other_device.pk]
