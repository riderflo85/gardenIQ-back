import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory
from gardeniq.hardware.serializers import SensorCategoryReadOnlySerializer
from gardeniq.hardware.serializers import SensorCategorySerializer
from gardeniq.hardware.serializers import SensorDetailReadOnlySerializer
from gardeniq.hardware.serializers import SensorListReadOnlySerializer
from gardeniq.hardware.serializers import SensorSerializer

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_serial_ports(mocker):
    """Mock serial port discovery to avoid hardware dependency in tests."""
    mock = mocker.patch("gardeniq.hardware.serializers.device.get_serial_port_choices")
    mock.return_value = ["/dev/ttyUSB0", "/dev/ttyUSB1"]
    return mock


@pytest.fixture
def device_status(db):
    return Status.objects.create(name="Generic", tag="device-generic", color="#123456")


@pytest.fixture
def device(device_status):
    return Device.objects.create(
        name="Test Device",
        uid="AABBCCDDEEFF0011",
        path="/dev/ttyUSB0",
        status=device_status,
    )


@pytest.fixture
def channel(db):
    return Channel.objects.create(name="Analog")


@pytest.fixture
def pin(device, channel):
    p = Pin.objects.create(
        device=device,
        channel_choiced=channel,
        pin_number=1,
    )
    p.channels_available.set([channel])
    return p


@pytest.fixture
def sensor_category(db):
    return SensorCategory.objects.create(name="Temperature", unity_value="°C")


@pytest.fixture
def sensor(sensor_category, device, pin):
    return Sensor.objects.create(
        name="Main Temp Sensor",
        category=sensor_category,
        device=device,
        pin=pin,
    )


# ─── SensorCategorySerializer ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestSensorCategorySerializer:
    """Tests for SensorCategorySerializer (writable)."""

    def test_valid_serializer(self):
        """
        GIVEN: valid data for a SensorCategory
        WHEN: validating through SensorCategorySerializer
        THEN: the serializer is valid and data matches the input
        """
        # GIVEN
        data = {"name": "Temperature", "unity_value": "°C", "pin_init_cfg": {"mode": "input"}}
        expected = {"name": "Temperature", "unity_value": "°C", "pin_init_cfg": {"mode": "input"}}

        # WHEN
        serializer = SensorCategorySerializer(data=data)

        # THEN
        assert serializer.is_valid()
        assert serializer.data == expected

    def test_create(self):
        """
        GIVEN: valid data for a SensorCategory
        WHEN: saving the serializer
        THEN: a SensorCategory is created with the correct values
        """
        # GIVEN
        data = {"name": "Humidity", "unity_value": "%", "pin_init_cfg": {}}

        # WHEN
        serializer = SensorCategorySerializer(data=data)
        assert serializer.is_valid()
        category = serializer.save()

        # THEN
        assert isinstance(category, SensorCategory)
        assert SensorCategory.objects.count() == 1
        assert category.name == data["name"]
        assert category.unity_value == data["unity_value"]
        assert category.pin_init_cfg == data["pin_init_cfg"]

    def test_create_with_nested_pin_init_cfg(self):
        """
        GIVEN: valid data with a nested pin_init_cfg
        WHEN: saving the serializer
        THEN: the SensorCategory stores the nested configuration correctly
        """
        # GIVEN
        cfg = {"mode": "input", "settings": {"pull": "up", "value": 0}}
        data = {"name": "Light", "unity_value": "lux", "pin_init_cfg": cfg}

        # WHEN
        serializer = SensorCategorySerializer(data=data)
        assert serializer.is_valid()
        category = serializer.save()

        # THEN
        assert category.pin_init_cfg == cfg

    def test_update(self, sensor_category):
        """
        GIVEN: an existing SensorCategory and new data
        WHEN: updating through SensorCategorySerializer
        THEN: the category is updated with the new values
        """
        # GIVEN
        updated_data = {"name": "Updated Temperature", "unity_value": "°F", "pin_init_cfg": {"mode": "input"}}

        # WHEN
        serializer = SensorCategorySerializer(instance=sensor_category, data=updated_data)
        assert serializer.is_valid()
        category = serializer.save()

        # THEN
        assert isinstance(category, SensorCategory)
        assert SensorCategory.objects.count() == 1
        assert category.name == updated_data["name"]
        assert category.unity_value == updated_data["unity_value"]
        assert category.pin_init_cfg == updated_data["pin_init_cfg"]

    def test_serialized_instance(self, sensor_category):
        """
        GIVEN: an existing SensorCategory instance
        WHEN: serializing with SensorCategorySerializer
        THEN: the serializer data contains all expected fields with correct values
        """
        # GIVEN
        expected = {
            "id": sensor_category.pk,
            "name": sensor_category.name,
            "unity_value": sensor_category.unity_value,
            "pin_init_cfg": sensor_category.pin_init_cfg,
        }

        # WHEN
        serializer = SensorCategorySerializer(instance=sensor_category)

        # THEN
        assert serializer.data == expected


# ─── SensorCategoryReadOnlySerializer ─────────────────────────────────────────


@pytest.mark.django_db
class TestSensorCategoryReadOnlySerializer:
    """Tests for SensorCategoryReadOnlySerializer (read-only)."""

    def test_cannot_save(self):
        """
        GIVEN: valid data for a SensorCategory
        WHEN: attempting to save a read-only serializer
        THEN: a NotImplementedError is raised and nothing is created
        """
        # GIVEN
        count_before = SensorCategory.objects.count()
        data = {"name": "Temperature", "unity_value": "°C", "pin_init_cfg": {}}

        # WHEN
        serializer = SensorCategoryReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        assert SensorCategory.objects.count() == count_before

    def test_cannot_update(self, sensor_category):
        """
        GIVEN: an existing SensorCategory and updated data
        WHEN: attempting to save a read-only serializer with an instance
        THEN: a NotImplementedError is raised and the category is not modified
        """
        # GIVEN
        original_name = sensor_category.name
        data = {"name": "Updated Temperature", "unity_value": "°F", "pin_init_cfg": {}}

        # WHEN
        serializer = SensorCategoryReadOnlySerializer(instance=sensor_category, data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        refreshed = SensorCategory.objects.get(pk=sensor_category.pk)
        assert refreshed.name == original_name

    def test_serialized_instance(self, sensor_category):
        """
        GIVEN: an existing SensorCategory instance
        WHEN: serializing with SensorCategoryReadOnlySerializer
        THEN: the serializer data matches the expected representation
        """
        # GIVEN
        expected = {
            "id": sensor_category.pk,
            "name": sensor_category.name,
            "unity_value": sensor_category.unity_value,
            "pin_init_cfg": sensor_category.pin_init_cfg,
        }

        # WHEN
        serializer = SensorCategoryReadOnlySerializer(instance=sensor_category)

        # THEN
        assert serializer.data == expected


# ─── SensorSerializer ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSensorSerializer:
    """Tests for SensorSerializer (writable)."""

    def test_valid_serializer(self, sensor_category, device, pin):
        """
        GIVEN: valid data using PKs for all related objects
        WHEN: validating through SensorSerializer
        THEN: the serializer is valid and data contains the correct PKs
        """
        # GIVEN
        data = {
            "name": "Main Temp Sensor",
            "category": sensor_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }
        expected = {
            "name": "Main Temp Sensor",
            "category": sensor_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = SensorSerializer(data=data)

        # THEN
        assert serializer.is_valid()
        assert serializer.data == expected

    def test_create(self, sensor_category, device, pin):
        """
        GIVEN: valid data for a Sensor
        WHEN: saving the serializer
        THEN: a Sensor is created with the correct name and linked objects
        """
        # GIVEN
        data = {
            "name": "Main Temp Sensor",
            "category": sensor_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = SensorSerializer(data=data)
        assert serializer.is_valid()
        s = serializer.save()

        # THEN
        assert isinstance(s, Sensor)
        assert Sensor.objects.count() == 1
        assert s.name == data["name"]
        assert s.category == sensor_category
        assert s.device == device
        assert s.pin == pin

    def test_update(self, sensor, device, channel):
        """
        GIVEN: an existing Sensor and updated data with new related objects
        WHEN: updating through SensorSerializer
        THEN: the Sensor is updated with the new values
        """
        # GIVEN
        new_category = SensorCategory.objects.create(name="Humidity", unity_value="%", pin_init_cfg={})
        new_pin = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        updated_data = {
            "name": "Updated Temp Sensor",
            "category": new_category.pk,
            "device": device.pk,
            "pin": new_pin.pk,
        }

        # WHEN
        serializer = SensorSerializer(instance=sensor, data=updated_data)
        assert serializer.is_valid()
        s = serializer.save()

        # THEN
        assert isinstance(s, Sensor)
        assert Sensor.objects.count() == 1
        assert s.name == updated_data["name"]
        assert s.category == new_category
        assert s.pin == new_pin

    def test_serialized_instance(self, sensor, sensor_category, device, pin):
        """
        GIVEN: an existing Sensor instance
        WHEN: serializing with SensorSerializer
        THEN: the serializer data contains the PKs of all related objects
        """
        # GIVEN
        expected = {
            "id": sensor.pk,
            "name": sensor.name,
            "category": sensor_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = SensorSerializer(instance=sensor)

        # THEN
        assert serializer.data == expected


# ─── SensorListReadOnlySerializer ─────────────────────────────────────────────


@pytest.mark.django_db
class TestSensorListReadOnlySerializer:
    """Tests for SensorListReadOnlySerializer (read-only with nested objects)."""

    def test_cannot_save(self, sensor_category, device, pin):
        """
        GIVEN: valid data for a Sensor
        WHEN: attempting to save a read-only serializer
        THEN: a NotImplementedError is raised and nothing is created
        """
        # GIVEN
        count_before = Sensor.objects.count()
        data = {
            "name": "Main Temp Sensor",
            "category": sensor_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = SensorListReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        assert Sensor.objects.count() == count_before

    def test_cannot_update(self, sensor, sensor_category, device, pin):
        """
        GIVEN: an existing Sensor and updated data
        WHEN: attempting to save a read-only serializer with an instance
        THEN: a NotImplementedError is raised and the Sensor is not modified
        """
        # GIVEN
        original_name = sensor.name
        data = {
            "name": "Updated Temp Sensor",
            "category": sensor_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = SensorListReadOnlySerializer(instance=sensor, data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        refreshed = Sensor.objects.get(pk=sensor.pk)
        assert refreshed.name == original_name

    def test_serialized_instance(self, sensor, sensor_category, device, pin, channel, device_status):
        """
        GIVEN: an existing Sensor instance with all related objects
        WHEN: serializing with SensorListReadOnlySerializer
        THEN: the related objects are represented in their minimal nested form
        """
        # GIVEN
        expected = {
            "id": sensor.pk,
            "name": sensor.name,
            "category": {
                "id": sensor_category.pk,
                "name": sensor_category.name,
            },
            "device": {
                "id": device.pk,
                "name": device.name,
                "status": {
                    "id": device_status.pk,
                    "name": device_status.name,
                    "description": device_status.description,
                    "tag": device_status.tag,
                    "color": device_status.color,
                },
            },
            "pin": {
                "id": pin.pk,
                "pin_number": pin.pin_number,
                "channel_choiced": channel.name,
            },
        }

        # WHEN
        serializer = SensorListReadOnlySerializer(instance=sensor)

        # THEN
        assert serializer.data == expected

    def test_serialized_multiple_instances(self, sensor, sensor_category, device, channel):
        """
        GIVEN: multiple existing Sensor instances
        WHEN: serializing with SensorListReadOnlySerializer using many=True
        THEN: all instances appear in the serialized list with correct names
        """
        # GIVEN
        second_pin = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        second_pin.channels_available.set([channel])
        second_sensor = Sensor.objects.create(
            name="Humidity Sensor",
            category=sensor_category,
            device=device,
            pin=second_pin,
        )
        queryset = Sensor.objects.order_by("pk")

        # WHEN
        serializer = SensorListReadOnlySerializer(instance=queryset, many=True)

        # THEN
        assert len(serializer.data) == 2
        names = [item["name"] for item in serializer.data]
        assert sensor.name in names
        assert second_sensor.name in names


# ─── SensorDetailReadOnlySerializer ───────────────────────────────────────────


@pytest.mark.django_db
class TestSensorDetailReadOnlySerializer:
    """Tests for SensorDetailReadOnlySerializer (read-only with full device details)."""

    def test_cannot_save(self, sensor_category, device, pin, mock_serial_ports):
        """
        GIVEN: valid data for a Sensor
        WHEN: attempting to save a read-only serializer
        THEN: a NotImplementedError is raised and nothing is created
        """
        # GIVEN
        count_before = Sensor.objects.count()
        data = {
            "name": "Main Temp Sensor",
            "category": sensor_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = SensorDetailReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        assert Sensor.objects.count() == count_before

    def test_serialized_instance_sensor_and_category_fields(
        self, sensor, sensor_category, pin, channel, mock_serial_ports
    ):
        """
        GIVEN: an existing Sensor instance
        WHEN: serializing with SensorDetailReadOnlySerializer
        THEN: id, name, category and pin fields are correctly represented
        """
        # GIVEN
        serializer = SensorDetailReadOnlySerializer(instance=sensor)

        # WHEN
        data = serializer.data

        # THEN
        assert data["id"] == sensor.pk
        assert data["name"] == sensor.name
        assert data["category"] == {
            "id": sensor_category.pk,
            "name": sensor_category.name,
        }
        assert data["pin"] == {
            "id": pin.pk,
            "pin_number": pin.pin_number,
            "channel_choiced": channel.name,
        }

    def test_serialized_instance_device_detail_fields(self, sensor, device, device_status, mock_serial_ports):
        """
        GIVEN: an existing Sensor instance with a Device
        WHEN: serializing with SensorDetailReadOnlySerializer
        THEN: the nested device contains full detail fields including uid, firmware versions and status
        """
        # GIVEN
        serializer = SensorDetailReadOnlySerializer(instance=sensor)

        # WHEN
        device_data = dict(serializer.data["device"])

        # THEN - last_seen is auto_now and dynamic, check separately
        last_seen = device_data.pop("last_seen")
        assert isinstance(last_seen, str)
        assert device_data == {
            "id": device.pk,
            "name": device.name,
            "description": device.description,
            "uid": device.uid,
            "path": device.path,
            "gd_firmware_version": device.gd_firmware_version,
            "mp_firmware_version": device.mp_firmware_version,
            "need_upgrade": device.need_upgrade,
            "status": {
                "id": device_status.pk,
                "name": device_status.name,
                "description": device_status.description,
                "tag": device_status.tag,
                "color": device_status.color,
            },
        }
