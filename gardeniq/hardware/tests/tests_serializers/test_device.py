import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Device
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

    def test_valid_serializer(self, mock_serial_ports, status_device):
        # GIVEN
        data = {
            "name": "Garden Sensor 1",
            "description": "Main garden sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
        }
        expected = {
            "name": "Garden Sensor 1",
            "description": "Main garden sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert ser.is_valid()
        assert ser.data == expected

    def test_valid_serializer_without_description(self, mock_serial_ports, status_device):
        # GIVEN
        data = {
            "name": "Garden Sensor 2",
            "path": "/dev/ttyUSB1",
            "status": status_device.pk,
        }
        expected = {
            "name": "Garden Sensor 2",
            "path": "/dev/ttyUSB1",
            "status": status_device.pk,
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert ser.is_valid()
        assert ser.data == expected

    def test_create_device(self, mock_serial_ports, status_device):
        # GIVEN
        data = {
            "name": "Garden Sensor 1",
            "description": "Main garden sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
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

    def test_create_device_without_description(self, mock_serial_ports, status_device):
        # GIVEN
        data = {
            "name": "Garden Sensor 2",
            "path": "/dev/ttyACM0",
            "status": status_device.pk,
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

    def test_update_device(self, mock_serial_ports, status_device):
        # GIVEN
        device = Device.objects.create(
            name="Old Name",
            description="Old description",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
        )
        updated_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "path": "/dev/ttyUSB1",
            "status": status_device.pk,
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

    def test_update_device_change_status(self, mock_serial_ports, status_device):
        # GIVEN
        new_status = Status.objects.create(name="Inactive", tag="device-inactive", color="#FF0000")
        device = Device.objects.create(
            name="Garden Sensor",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
        )
        updated_data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB0",
            "status": new_status.pk,
        }

        # WHEN
        ser = DeviceSerializer(instance=device, data=updated_data)
        assert ser.is_valid()
        ser.save()
        device.refresh_from_db()

        # THEN
        assert device.status == new_status

    def test_readonly_fields(self, mock_serial_ports, status_device):
        # GIVEN
        data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
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

    def test_errors_missing_required_fields(self, mock_serial_ports):
        # GIVEN
        data = {
            "description": "Description without name or path",
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert ser.errors
        assert "name" in ser.errors
        assert "path" in ser.errors
        assert "status" in ser.errors

    def test_errors_invalid_path_not_in_choices(self, mock_serial_ports, status_device):
        # GIVEN
        data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB5",  # Not in mock choices
            "status": status_device.pk,
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

    def test_errors_empty_name(self, mock_serial_ports, status_device):
        # GIVEN
        data = {
            "name": "",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
        }

        # WHEN
        ser = DeviceSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "name" in ser.errors

    def test_serial_port_choices_initialized(self, mock_serial_ports, status_device):
        # GIVEN
        data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
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

    def test_cannot_create_device(self, mock_serial_ports, status_device):
        # GIVEN
        device_count_before = Device.objects.count()
        data = {
            "name": "Garden Sensor",
            "path": "/dev/ttyUSB0",
            "status": status_device.pk,
        }

        # WHEN
        ser = DeviceDetailReadOnlySerializer(data=data)
        assert ser.is_valid()
        with pytest.raises(NotImplementedError):
            ser.save()

        # THEN
        assert Device.objects.count() == device_count_before

    def test_cannot_update_device(self, mock_serial_ports, status_device):
        # GIVEN
        device = Device.objects.create(
            name="Garden Sensor",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
        )
        updated_data = {
            "name": "Updated Name",
            "path": "/dev/ttyUSB1",
            "status": status_device.pk,
        }

        # WHEN
        ser = DeviceDetailReadOnlySerializer(instance=device, data=updated_data)
        assert ser.is_valid()
        with pytest.raises(NotImplementedError):
            ser.save()

    def test_serialize_device(self, mock_serial_ports, status_device):
        # GIVEN
        device = Device.objects.create(
            name="Garden Sensor",
            description="Main garden sensor",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
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
            "gd_firmware_version": "1.2.3",
            "mp_firmware_version": "1.21.0",
        }

        # WHEN
        ser = DeviceDetailReadOnlySerializer(instance=device)
        ser_data = dict(ser.data)  # Convert to dict to avoid typing warnings

        # THEN
        assert "last_seen" in ser_data
        ser_data.pop("last_seen")  # Remove last_seen for comparison
        assert ser_data == expected_data

    def test_serialize_device_without_description(self, mock_serial_ports, status_device):
        # GIVEN
        device = Device.objects.create(
            name="Garden Sensor",
            uid="12AB34567890DEAD",
            path="/dev/ttyUSB0",
            status=status_device,
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
            "gd_firmware_version": "",
            "mp_firmware_version": "",
        }

        # WHEN
        ser = DeviceDetailReadOnlySerializer(instance=device)
        ser_data = dict(ser.data)  # Convert to dict to avoid typing warnings

        # THEN
        assert "last_seen" in ser_data
        ser_data.pop("last_seen")  # Remove last_seen for comparison
        assert ser_data == expected_data
