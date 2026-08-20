from django.db.models import ProtectedError

import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory

# ─── Fixtures ─────────────────────────────────────────────────────────────────


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


# ─── SensorCategory Tests ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSensorCategoryCreation:
    """Tests for SensorCategory model creation."""

    def test_create_with_name_only(self):
        """
        GIVEN: a name for a SensorCategory
        WHEN: creating a SensorCategory without specifying unity_value or pin_init_cfg
        THEN: the SensorCategory is created with an empty unity_value and an empty dict as default pin_init_cfg
        """
        # GIVEN / WHEN
        category = SensorCategory.objects.create(name="Humidity")

        # THEN
        assert category.pk is not None
        assert category.name == "Humidity"
        assert category.unity_value == ""
        assert category.pin_init_cfg == {}

    def test_create_with_unity_value(self):
        """
        GIVEN: a name and a unity_value
        WHEN: creating a SensorCategory with those values
        THEN: the SensorCategory is created with the correct unity_value
        """
        # GIVEN / WHEN
        category = SensorCategory.objects.create(name="Temperature", unity_value="°C")

        # THEN
        assert category.pk is not None
        assert category.unity_value == "°C"

    def test_create_with_pin_init_cfg(self):
        """
        GIVEN: a name and a custom pin_init_cfg dict
        WHEN: creating a SensorCategory with this configuration
        THEN: the SensorCategory is created with the provided configuration
        """
        # GIVEN
        cfg = {"mode": "input", "pull": "up"}

        # WHEN
        category = SensorCategory.objects.create(name="Light", pin_init_cfg=cfg)

        # THEN
        assert category.pk is not None
        assert category.pin_init_cfg == cfg

    def test_create_multiple_categories(self):
        """
        GIVEN: data for multiple SensorCategories
        WHEN: creating multiple SensorCategories
        THEN: all categories are persisted in the database
        """
        # GIVEN
        names = ["Temperature", "Humidity", "Light"]

        # WHEN
        for name in names:
            SensorCategory.objects.create(name=name)

        # THEN
        assert SensorCategory.objects.count() == len(names)


@pytest.mark.django_db
class TestSensorCategoryUnityValue:
    """Tests for SensorCategory unity_value field."""

    def test_unity_value_defaults_to_empty_string(self):
        """
        GIVEN: no unity_value provided
        WHEN: creating a SensorCategory without specifying unity_value
        THEN: the field defaults to an empty string
        """
        # GIVEN / WHEN
        category = SensorCategory.objects.create(name="Pressure")

        # THEN
        assert category.unity_value == ""

    def test_unity_value_can_be_updated(self, sensor_category):
        """
        GIVEN: an existing SensorCategory
        WHEN: updating the unity_value
        THEN: the new value is persisted correctly
        """
        # GIVEN
        new_unity = "hPa"

        # WHEN
        sensor_category.unity_value = new_unity
        sensor_category.save()

        # THEN
        refreshed = SensorCategory.objects.get(pk=sensor_category.pk)
        assert refreshed.unity_value == new_unity

    def test_unity_value_accepts_various_formats(self):
        """
        GIVEN: different unity_value formats (symbols, abbreviations)
        WHEN: creating SensorCategories with each value
        THEN: each value is stored and retrieved correctly
        """
        # GIVEN
        unity_values = ["°C", "%", "lux", "pH", "m/s"]

        # WHEN / THEN
        for unity in unity_values:
            category = SensorCategory.objects.create(name=f"Sensor {unity}", unity_value=unity)
            refreshed = SensorCategory.objects.get(pk=category.pk)
            assert refreshed.unity_value == unity


@pytest.mark.django_db
class TestSensorCategoryPinInitCfg:
    """Tests for SensorCategory pin_init_cfg field."""

    def test_pin_init_cfg_defaults_to_empty_dict(self):
        """
        GIVEN: no pin_init_cfg value
        WHEN: creating a SensorCategory without specifying pin_init_cfg
        THEN: the field defaults to an empty dict
        """
        # GIVEN / WHEN
        category = SensorCategory.objects.create(name="Humidity")

        # THEN
        assert category.pin_init_cfg == {}

    def test_pin_init_cfg_can_be_updated(self, sensor_category):
        """
        GIVEN: an existing SensorCategory with an empty pin_init_cfg
        WHEN: updating the pin_init_cfg with new values
        THEN: the new configuration is persisted correctly
        """
        # GIVEN
        new_cfg = {"mode": "input", "pull": "up"}

        # WHEN
        sensor_category.pin_init_cfg = new_cfg
        sensor_category.save()

        # THEN
        refreshed = SensorCategory.objects.get(pk=sensor_category.pk)
        assert refreshed.pin_init_cfg == new_cfg

    def test_pin_init_cfg_accepts_nested_json(self):
        """
        GIVEN: a nested JSON structure as pin_init_cfg
        WHEN: creating a SensorCategory with this configuration
        THEN: the nested structure is stored and retrieved correctly
        """
        # GIVEN
        nested_cfg = {"settings": {"mode": "input", "options": {"pull": "up", "value": 0}}}

        # WHEN
        category = SensorCategory.objects.create(
            name="Advanced Sensor",
            pin_init_cfg=nested_cfg,
        )

        # THEN
        refreshed = SensorCategory.objects.get(pk=category.pk)
        assert refreshed.pin_init_cfg == nested_cfg


@pytest.mark.django_db
class TestSensorCategoryRelations:
    """Tests for SensorCategory reverse relation to Sensor."""

    def test_sensors_reverse_relation_returns_linked_sensor(self, sensor, sensor_category):
        """
        GIVEN: a Sensor linked to a SensorCategory
        WHEN: accessing the sensors reverse relation on the category
        THEN: the related Sensor is returned
        """
        # GIVEN - fixtures create the Sensor linked to the category

        # WHEN
        related = sensor_category.sensors.all()

        # THEN
        assert related.count() == 1
        assert sensor in related

    def test_sensors_reverse_relation_is_empty_when_no_sensors(self, sensor_category):
        """
        GIVEN: a SensorCategory with no Sensors
        WHEN: accessing the sensors reverse relation
        THEN: an empty queryset is returned
        """
        # GIVEN - no Sensor is created

        # WHEN
        related = sensor_category.sensors.all()

        # THEN
        assert related.count() == 0


@pytest.mark.django_db
class TestSensorCategoryDeletion:
    """Tests for SensorCategory deletion behavior."""

    def test_delete_category_without_sensors(self, sensor_category):
        """
        GIVEN: a SensorCategory with no Sensors
        WHEN: deleting the SensorCategory
        THEN: the SensorCategory is removed from the database
        """
        # GIVEN
        category_id = sensor_category.pk

        # WHEN
        sensor_category.delete()

        # THEN
        assert not SensorCategory.objects.filter(pk=category_id).exists()

    def test_delete_category_raises_protected_error_when_sensors_exist(self, sensor, sensor_category):
        """
        GIVEN: a SensorCategory that has at least one Sensor
        WHEN: attempting to delete the SensorCategory
        THEN: a ProtectedError is raised and the Sensor is preserved
        """
        # GIVEN - fixture creates a Sensor linked to the category

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            sensor_category.delete()

        assert Sensor.objects.filter(pk=sensor.pk).exists()


# ─── Sensor Tests ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSensorCreation:
    """Tests for Sensor model creation."""

    def test_create_sensor_with_all_fields(self, sensor_category, device, pin):
        """
        GIVEN: a name, a SensorCategory, a Device and a Pin
        WHEN: creating a Sensor with all required fields
        THEN: the Sensor is created with the correct values
        """
        # GIVEN / WHEN
        s = Sensor.objects.create(
            name="Main Temp Sensor",
            category=sensor_category,
            device=device,
            pin=pin,
        )

        # THEN
        assert s.pk is not None
        assert s.name == "Main Temp Sensor"
        assert s.category == sensor_category
        assert s.device == device
        assert s.pin == pin

    def test_create_multiple_sensors_for_same_device(self, sensor_category, device, channel):
        """
        GIVEN: a Device with multiple Pins and a SensorCategory
        WHEN: creating multiple Sensors linked to the same Device
        THEN: all Sensors are persisted in the database
        """
        # GIVEN
        pin1 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        pin2 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=3)

        # WHEN
        Sensor.objects.create(name="Temp Sensor", category=sensor_category, device=device, pin=pin1)
        Sensor.objects.create(name="Humidity Sensor", category=sensor_category, device=device, pin=pin2)

        # THEN
        assert Sensor.objects.count() == 2


@pytest.mark.django_db
class TestSensorRelations:
    """Tests for Sensor foreign key relationships."""

    def test_category_relation_returns_correct_category(self, sensor, sensor_category):
        """
        GIVEN: a Sensor linked to a SensorCategory
        WHEN: accessing the category attribute
        THEN: the correct SensorCategory is returned
        """
        # GIVEN - fixture creates the Sensor with the category

        # WHEN
        result = sensor.category

        # THEN
        assert result == sensor_category

    def test_device_relation_returns_correct_device(self, sensor, device):
        """
        GIVEN: a Sensor linked to a Device
        WHEN: accessing the device attribute
        THEN: the correct Device is returned
        """
        # GIVEN - fixture creates the Sensor with the device

        # WHEN
        result = sensor.device

        # THEN
        assert result == device

    def test_pin_relation_returns_correct_pin(self, sensor, pin):
        """
        GIVEN: a Sensor linked to a Pin
        WHEN: accessing the pin attribute
        THEN: the correct Pin is returned
        """
        # GIVEN - fixture creates the Sensor with the pin

        # WHEN
        result = sensor.pin

        # THEN
        assert result == pin

    def test_device_reverse_relation_includes_sensor(self, sensor, device):
        """
        GIVEN: a Sensor linked to a Device
        WHEN: accessing the sensors reverse relation on the Device
        THEN: the related Sensor is returned
        """
        # GIVEN - fixture creates the Sensor linked to the device

        # WHEN
        related = device.sensors.all()

        # THEN
        assert related.count() == 1
        assert sensor in related

    def test_pin_reverse_relation_includes_sensor(self, sensor, pin):
        """
        GIVEN: a Sensor linked to a Pin
        WHEN: accessing the sensors reverse relation on the Pin
        THEN: the related Sensor is returned
        """
        # GIVEN - fixture creates the Sensor linked to the pin

        # WHEN
        related = pin.sensors.all()

        # THEN
        assert related.count() == 1
        assert sensor in related


@pytest.mark.django_db
class TestSensorProtect:
    """Tests for Sensor PROTECT behavior on related object deletion."""

    def test_delete_category_raises_protected_error(self, sensor, sensor_category):
        """
        GIVEN: a Sensor linked to a SensorCategory
        WHEN: attempting to delete the SensorCategory
        THEN: a ProtectedError is raised and the Sensor is preserved
        """
        # GIVEN - fixture creates the Sensor linked to the category

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            sensor_category.delete()

        assert Sensor.objects.filter(pk=sensor.pk).exists()

    def test_delete_device_raises_protected_error(self, sensor, device):
        """
        GIVEN: a Sensor linked to a Device
        WHEN: attempting to delete the Device
        THEN: a ProtectedError is raised and the Sensor is preserved
        """
        # GIVEN - fixture creates the Sensor linked to the device

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            device.delete()

        assert Sensor.objects.filter(pk=sensor.pk).exists()

    def test_delete_pin_raises_protected_error(self, sensor, pin):
        """
        GIVEN: a Sensor linked to a Pin
        WHEN: attempting to delete the Pin
        THEN: a ProtectedError is raised and the Sensor is preserved
        """
        # GIVEN - fixture creates the Sensor linked to the pin

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            pin.delete()

        assert Sensor.objects.filter(pk=sensor.pk).exists()


@pytest.mark.django_db
class TestSensorUpdate:
    """Tests for Sensor model update operations."""

    def test_update_name(self, sensor):
        """
        GIVEN: an existing Sensor
        WHEN: updating its name
        THEN: the name is modified correctly in the database
        """
        # GIVEN
        new_name = "Updated Temp Sensor"

        # WHEN
        sensor.name = new_name
        sensor.save()

        # THEN
        updated = Sensor.objects.get(pk=sensor.pk)
        assert updated.name == new_name

    def test_update_category(self, sensor):
        """
        GIVEN: an existing Sensor and a new SensorCategory
        WHEN: assigning the new category to the Sensor
        THEN: the category FK is updated correctly in the database
        """
        # GIVEN
        new_category = SensorCategory.objects.create(name="Humidity", unity_value="%")

        # WHEN
        sensor.category = new_category
        sensor.save()

        # THEN
        updated = Sensor.objects.get(pk=sensor.pk)
        assert updated.category == new_category

    def test_update_pin(self, sensor, device, channel):
        """
        GIVEN: an existing Sensor and a new Pin on the same Device
        WHEN: assigning the new Pin to the Sensor
        THEN: the pin FK is updated correctly in the database
        """
        # GIVEN
        new_pin = Pin.objects.create(device=device, channel_choiced=channel, pin_number=5)

        # WHEN
        sensor.pin = new_pin
        sensor.save()

        # THEN
        updated = Sensor.objects.get(pk=sensor.pk)
        assert updated.pin == new_pin


@pytest.mark.django_db
class TestSensorDeletion:
    """Tests for Sensor model deletion."""

    def test_delete_sensor(self, sensor):
        """
        GIVEN: an existing Sensor
        WHEN: deleting this Sensor
        THEN: the Sensor no longer exists in the database
        """
        # GIVEN
        sensor_id = sensor.pk

        # WHEN
        sensor.delete()

        # THEN
        assert not Sensor.objects.filter(pk=sensor_id).exists()

    def test_delete_sensor_does_not_delete_category(self, sensor, sensor_category):
        """
        GIVEN: an existing Sensor linked to a SensorCategory
        WHEN: deleting the Sensor
        THEN: the SensorCategory is not deleted
        """
        # GIVEN
        category_id = sensor_category.pk

        # WHEN
        sensor.delete()

        # THEN
        assert SensorCategory.objects.filter(pk=category_id).exists()

    def test_delete_sensor_does_not_delete_device(self, sensor, device):
        """
        GIVEN: an existing Sensor linked to a Device
        WHEN: deleting the Sensor
        THEN: the Device is not deleted
        """
        # GIVEN
        device_id = device.pk

        # WHEN
        sensor.delete()

        # THEN
        assert Device.objects.filter(pk=device_id).exists()

    def test_delete_sensor_does_not_delete_pin(self, sensor, pin):
        """
        GIVEN: an existing Sensor linked to a Pin
        WHEN: deleting the Sensor
        THEN: the Pin is not deleted
        """
        # GIVEN
        pin_id = pin.pk

        # WHEN
        sensor.delete()

        # THEN
        assert Pin.objects.filter(pk=pin_id).exists()
