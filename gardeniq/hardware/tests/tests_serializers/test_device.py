import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.serializers import DeviceCategoryDetailReadOnlySerializer
from gardeniq.hardware.serializers import DeviceCategoryListReadOnlySerializer
from gardeniq.hardware.serializers import DeviceCategorySeederSerializer
from gardeniq.hardware.serializers import DeviceCategorySerializer
from gardeniq.hardware.serializers import DeviceDetailReadOnlySerializer
from gardeniq.hardware.serializers import DeviceSerializer


@pytest.fixture
def mock_serial_ports(mocker):
    """Mock the get_serial_port_choices function to return test serial ports."""
    mock = mocker.patch("gardeniq.hardware.serializers.device.get_serial_port_choices")
    mock.return_value = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0"]
    return mock


@pytest.fixture
def status_device(db):
    """Create a status for device tests."""
    return Status.objects.create(name="Active", tag="device-active", color="#00FF00")


@pytest.mark.django_db
class TestDeviceSerializer:

    def test_valid_serializer(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        data = {
            "name": "Garden Sensor 1",
            "description": "Main garden sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }
        expected = {
            "name": "Garden Sensor 1",
            "description": "Main garden sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert ser.is_valid()
        assert ser.data == expected

    def test_valid_serializer_without_description(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        data = {
            "name": "Garden Sensor 2",
            "path": "/dev/ttyUSB1",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }
        expected = {
            "name": "Garden Sensor 2",
            "path": "/dev/ttyUSB1",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert ser.is_valid()
        assert ser.data == expected

    def test_create_device(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        data = {
            "name": "Garden Sensor 1",
            "description": "Main garden sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceSerializer(data=data)
        assert ser.is_valid()
        device = ser.save(uid="12AB34567890DEAD")

        # THEN
        assert isinstance(device, Device)
        assert Device.objects.count() == 1
        assert device.name == data["name"]
        assert device.description == data["description"]
        assert device.path == data["path"]
        assert device.status == status_device
        assert device.uid == "12AB34567890DEAD"

    def test_create_several_devices_without_uid(self, mock_serial_ports, status_device, device_category):
        """The API never sends a uid: several devices created this way are saved with a NULL uid."""
        # GIVEN
        data = {
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }
        first = DeviceSerializer(data={**data, "name": "Garden Sensor 1"})
        assert first.is_valid(), first.errors
        first.save()

        # WHEN
        second = DeviceSerializer(data={**data, "name": "Garden Sensor 2"})
        assert second.is_valid(), second.errors
        second.save()

        # THEN
        assert list(Device.objects.values_list("uid", flat=True)) == [None, None]
        assert second.data["uid"] is None

    def test_create_device_without_description(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        data = {
            "name": "Garden Sensor 2",
            "path": "/dev/ttyACM0",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceSerializer(data=data)
        assert ser.is_valid()
        device = ser.save(uid="ABCD1234567890EF")

        # THEN
        assert isinstance(device, Device)
        assert Device.objects.count() == 1
        assert device.name == data["name"]
        assert device.description == ""
        assert device.path == data["path"]
        assert device.status == status_device

    def test_update_device(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        device = Device.objects.create(
            name="Old Name",
            description="Old description",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
            category=device_category,
        )
        updated_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "path": "/dev/ttyUSB1",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceSerializer(instance=device, data=updated_data)
        assert ser.is_valid()
        device = ser.save()

        # THEN
        assert isinstance(device, Device)
        assert Device.objects.count() == 1
        assert device.name == updated_data["name"]
        assert device.description == updated_data["description"]
        assert device.path == updated_data["path"]
        assert device.status == status_device

    def test_update_device_change_status(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        new_status = Status.objects.create(name="Inactive", tag="device-inactive", color="#FF0000")
        device = Device.objects.create(
            name="Garden Sensor",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
            category=device_category,
        )
        updated_data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB0",
            "status": new_status.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceSerializer(instance=device, data=updated_data)
        assert ser.is_valid()
        ser.save()
        device.refresh_from_db()

        # THEN
        assert device.status == new_status

    def test_readonly_fields(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
            "uid": "FAKEFAKEFAKEFAKE",
            "gd_firmware_version": "1.0.0",
            "mp_firmware_version": "1.21.0",
        }

        # WHEN
        ser = DeviceSerializer(data=data)
        assert ser.is_valid()
        device = ser.save(uid="12AB34567890DEAD")

        # THEN
        # UID should be the one from save(), not from data
        assert device.uid == "12AB34567890DEAD"  # type: ignore
        # Firmware versions should be empty (read-only fields)
        assert device.gd_firmware_version == ""  # type: ignore
        assert device.mp_firmware_version == ""  # type: ignore
        assert device.need_upgrade is False  # type: ignore

    def test_errors_missing_required_fields(self, mock_serial_ports):
        # GIVEN
        data = {
            "description": "Description without required fields",
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert ser.errors
        assert "name" in ser.errors
        assert "path" not in ser.errors  # optional
        assert "status" in ser.errors
        assert "category" in ser.errors
        assert "communication_protocol" in ser.errors

    def test_errors_invalid_path_not_in_choices(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB5",  # Not in mock choices
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "path" in ser.errors

    def test_errors_invalid_status(self, mock_serial_ports):
        # GIVEN
        data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB0",
            "status": 999,  # Non-existent status
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "status" in ser.errors

    def test_errors_empty_name(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        data = {
            "name": "",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "name" in ser.errors

    def test_serial_port_choices_initialized(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }
        available_ports = {p: p for p in ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0"]}

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert ser.is_valid()
        # Verify that get_serial_port_choices was called during __init__
        mock_serial_ports.assert_called()
        # Verify that choices are set correctly
        assert ser.fields["path"].choices == available_ports  # type: ignore


@pytest.mark.django_db
class TestDeviceDetailReadOnlySerializer:

    def test_cannot_create_device(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        device_count_before = Device.objects.count()
        data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceDetailReadOnlySerializer(data=data)
        assert ser.is_valid()
        with pytest.raises(NotImplementedError):
            ser.save()

        # THEN
        assert Device.objects.count() == device_count_before

    def test_cannot_update_device(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        device = Device.objects.create(
            name="Garden Sensor",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
            category=device_category,
        )
        updated_data = {
            "name": "Updated Name",
            "path": "/dev/ttyUSB1",
            "status": status_device.pk,
            "category": device_category.pk,
            "communication_protocol": "USB",
        }

        # WHEN
        ser = DeviceDetailReadOnlySerializer(instance=device, data=updated_data)
        assert ser.is_valid()
        with pytest.raises(NotImplementedError):
            ser.save()

    def test_serialize_device(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        device = Device.objects.create(
            name="Garden Sensor",
            description="Main garden sensor",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
            category=device_category,
            gd_firmware_version="1.2.3",
            mp_firmware_version="1.21.0",
        )
        expected_status = {
            "id": status_device.pk,
            "name": "Active",
            "description": "",
            "tag": "device-active",
            "color": "#00FF00",
        }
        expected_data = {
            "id": device.pk,
            "name": "Garden Sensor",
            "description": "Main garden sensor",
            "uid": "12AB34567890DEAD",
            "path": "/dev/ttyUSB0",
            "status": expected_status,
            "category": {
                "id": device_category.pk,
                "name": "Pico",
                "description": "Pico board",
                "is_ready": True,
                "pins_configuration": VALID_PINS_CONFIGURATION,
            },
            "communication_protocol": "",
            "gd_firmware_version": "1.2.3",
            "mp_firmware_version": "1.21.0",
            "need_upgrade": False,
        }

        # WHEN
        ser = DeviceDetailReadOnlySerializer(instance=device)
        ser_data = dict(ser.data)  # Convert to dict to avoid typing warnings

        # THEN
        assert "last_seen" in ser_data
        ser_data.pop("last_seen")  # Remove last_seen for comparison
        assert ser_data == expected_data

    def test_serialize_device_without_description(self, mock_serial_ports, status_device, device_category):
        # GIVEN
        device = Device.objects.create(
            name="Garden Sensor",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
            category=device_category,
        )
        expected_data = {
            "id": device.pk,
            "name": "Garden Sensor",
            "description": "",
            "uid": "12AB34567890DEAD",
            "path": "/dev/ttyUSB0",
            "status": {
                "id": status_device.pk,
                "name": "Active",
                "description": "",
                "tag": "device-active",
                "color": "#00FF00",
            },
            "category": {
                "id": device_category.pk,
                "name": "Pico",
                "description": "Pico board",
                "is_ready": True,
                "pins_configuration": VALID_PINS_CONFIGURATION,
            },
            "communication_protocol": "",
            "gd_firmware_version": "",
            "mp_firmware_version": "",
            "need_upgrade": False,
        }

        # WHEN
        ser = DeviceDetailReadOnlySerializer(instance=device)
        ser_data = dict(ser.data)  # Convert to dict to avoid typing warnings

        # THEN
        assert "last_seen" in ser_data
        ser_data.pop("last_seen")  # Remove last_seen for comparison
        assert ser_data == expected_data


VALID_PINS_CONFIGURATION = {
    "available_channels": ["digit"],
    "digits": [{"name": "GP0", "pins": [0]}],
    "pwms": [],
    "analogs": [],
}


@pytest.fixture
def digit_channel(db):
    """Create the channel the datasheet below lists: saving a device creates its pins from it."""
    return Channel.objects.create(name="digit")


@pytest.fixture
def device_category(digit_channel):
    return DeviceCategory.objects.create(
        name="Pico", description="Pico board", pins_configuration=VALID_PINS_CONFIGURATION
    )


@pytest.mark.django_db
class TestDeviceCategorySerializer:

    def test_create_device_category(self):
        """Valid data creates a category."""
        # GIVEN
        data = {"name": "Pico", "description": "Pico board", "pins_configuration": VALID_PINS_CONFIGURATION}
        serializer = DeviceCategorySerializer(data=data)

        # WHEN
        assert serializer.is_valid(), serializer.errors
        category = serializer.save()

        # THEN
        assert category.pk is not None
        assert category.name == "Pico"
        assert category.description == "Pico board"
        assert category.pins_configuration == VALID_PINS_CONFIGURATION
        assert category.is_ready is True

    def test_description_is_optional(self):
        """The description can be omitted."""
        # GIVEN
        serializer = DeviceCategorySerializer(data={"name": "Pico", "pins_configuration": VALID_PINS_CONFIGURATION})

        # WHEN / THEN
        assert serializer.is_valid(), serializer.errors

    def test_name_is_required(self):
        """A category without name is refused."""
        # GIVEN
        serializer = DeviceCategorySerializer(data={"pins_configuration": VALID_PINS_CONFIGURATION})

        # WHEN / THEN
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_invalid_pins_configuration(self):
        """A pins_configuration that does not match the schema is refused on this field."""
        # GIVEN
        data = {"name": "Pico", "pins_configuration": {"available_channels": ["digit"]}}
        serializer = DeviceCategorySerializer(data=data)

        # WHEN / THEN
        assert not serializer.is_valid()
        assert "pins_configuration" in serializer.errors
        assert serializer.errors["pins_configuration"][0].startswith("Failed validation JSON schema")

    def test_missing_pins_configuration_is_refused(self):
        """pins_configuration is required."""
        # GIVEN
        serializer = DeviceCategorySerializer(data={"name": "Pico"})

        # WHEN / THEN
        assert not serializer.is_valid()
        assert "pins_configuration" in serializer.errors

    def test_is_ready_is_read_only(self):
        """is_ready sent by the client is ignored."""
        # GIVEN
        data = {"name": "Pico", "pins_configuration": VALID_PINS_CONFIGURATION, "is_ready": False}
        serializer = DeviceCategorySerializer(data=data)

        # WHEN
        assert serializer.is_valid(), serializer.errors
        category = serializer.save()

        # THEN
        assert category.is_ready is True

    def test_update_device_category(self, device_category):
        """An update changes the fields of the category."""
        # GIVEN
        new_cfg = {**VALID_PINS_CONFIGURATION, "analogs": [{"name": "ADC0", "pins": [26]}]}
        data = {"name": "Pico W", "description": "", "pins_configuration": new_cfg}
        serializer = DeviceCategorySerializer(instance=device_category, data=data)

        # WHEN
        assert serializer.is_valid(), serializer.errors
        serializer.save()

        # THEN
        device_category.refresh_from_db()
        assert device_category.name == "Pico W"
        assert device_category.description == ""
        assert device_category.pins_configuration == new_cfg


@pytest.mark.django_db
class TestDeviceCategoryReadOnlySerializers:

    def test_list_serializer_hides_pins_configuration(self, device_category):
        """The list serializer does not expose pins_configuration."""
        # WHEN
        data = DeviceCategoryListReadOnlySerializer(device_category).data

        # THEN
        assert "pins_configuration" not in data
        assert data["id"] == device_category.pk
        assert data["name"] == "Pico"
        assert data["description"] == "Pico board"
        assert data["is_ready"] is True

    def test_detail_serializer_exposes_pins_configuration(self, device_category):
        """The detail serializer exposes pins_configuration."""
        # WHEN
        data = DeviceCategoryDetailReadOnlySerializer(device_category).data

        # THEN
        assert data["name"] == "Pico"
        assert data["pins_configuration"] == VALID_PINS_CONFIGURATION

    @pytest.mark.parametrize(
        "serializer_class", [DeviceCategoryListReadOnlySerializer, DeviceCategoryDetailReadOnlySerializer]
    )
    def test_read_only_serializers_cannot_save(self, serializer_class, device_category):
        """The read-only serializers refuse to create or update."""
        # GIVEN
        data = {"name": "Other", "pins_configuration": VALID_PINS_CONFIGURATION}
        serializer = serializer_class(instance=device_category, data=data)
        serializer.is_valid()

        # WHEN / THEN
        with pytest.raises(NotImplementedError):
            serializer.save()


@pytest.mark.django_db
class TestDeviceCategorySeederSerializer:

    def test_create_with_seed_fields(self):
        """The seeder serializer writes seed_id and is_ready."""
        # GIVEN
        data = {"seed_id": 3, "is_ready": False, "name": "Pico", "pins_configuration": VALID_PINS_CONFIGURATION}
        serializer = DeviceCategorySeederSerializer(data=data)

        # WHEN
        assert serializer.is_valid(), serializer.errors
        category = serializer.save()

        # THEN
        assert category.seed_id == 3
        assert category.is_ready is False

    def test_seed_id_is_required(self):
        """The seeder serializer requires a seed_id."""
        # GIVEN
        serializer = DeviceCategorySeederSerializer(
            data={"name": "Pico", "pins_configuration": VALID_PINS_CONFIGURATION}
        )

        # WHEN / THEN
        assert not serializer.is_valid()
        assert "seed_id" in serializer.errors
