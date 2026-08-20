from rest_framework import status

import pytest

from gardeniq.base.models import Status
from gardeniq.base.utils.tests import ViewSetTestMixin
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory

# ─── SensorCategory View Tests ────────────────────────────────────────────────


@pytest.mark.django_db
class SensorCategoryViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "sensor-categories"
    MODEL = SensorCategory
    DATA_TO_DEFAULT_OBJ = {"name": "Default Category", "unity_value": "", "pin_init_cfg": {}}

    def generate_default_obj(self):
        cat1 = SensorCategory.objects.create(name="Temperature", unity_value="°C", pin_init_cfg={})
        cat2 = SensorCategory.objects.create(name="Humidity", unity_value="%", pin_init_cfg={})
        return cat1, cat2


@pytest.mark.django_db
class TestSensorCategoryAPIModelView(SensorCategoryViewSetTestConf):

    def test_list(self, authenticated_client, obj):
        """
        GIVEN: two existing SensorCategories
        WHEN: sending a GET request to the list endpoint
        THEN: the response contains both categories with the expected fields
        """
        # GIVEN
        cat1, cat2 = obj
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        names = [item["name"] for item in response.data["results"]]
        assert cat1.name in names
        assert cat2.name in names
        first = response.data["results"][0]
        assert "id" in first
        assert "name" in first
        assert "unity_value" in first
        assert "pin_init_cfg" in first

    def test_retrieve(self, authenticated_client, obj):
        """
        GIVEN: an existing SensorCategory
        WHEN: sending a GET request to the detail endpoint
        THEN: the response contains the correct category data
        """
        # GIVEN
        cat1, _ = obj
        url = self.get_url_detail(cat1)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == cat1.pk
        assert response.data["name"] == cat1.name
        assert response.data["unity_value"] == cat1.unity_value
        assert response.data["pin_init_cfg"] == cat1.pin_init_cfg

    def test_create(self, authenticated_client):
        """
        GIVEN: a valid payload for a SensorCategory
        WHEN: sending a POST request to the create endpoint
        THEN: the SensorCategory is created and the response contains the correct data
        """
        # GIVEN
        payload = {"name": "Light", "unity_value": "lux", "pin_init_cfg": {"mode": "input"}}
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == payload["name"]
        assert response.data["unity_value"] == payload["unity_value"]
        assert response.data["pin_init_cfg"] == payload["pin_init_cfg"]
        assert SensorCategory.objects.filter(name=payload["name"]).exists()

    def test_update(self, authenticated_client, obj):
        """
        GIVEN: an existing SensorCategory and updated data
        WHEN: sending a PUT request to the detail endpoint
        THEN: the SensorCategory is updated with the new values
        """
        # GIVEN
        cat1, _ = obj
        url = self.get_url_detail(cat1)
        update_data = {"name": "Updated Temperature", "unity_value": "°F", "pin_init_cfg": {"mode": "input"}}

        # WHEN
        response = authenticated_client.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == update_data["name"]
        assert response.data["unity_value"] == update_data["unity_value"]
        assert response.data["pin_init_cfg"] == update_data["pin_init_cfg"]
        cat1.refresh_from_db()
        assert cat1.name == update_data["name"]
        assert cat1.unity_value == update_data["unity_value"]
        assert cat1.pin_init_cfg == update_data["pin_init_cfg"]

    def test_delete(self, authenticated_client, obj):
        """
        GIVEN: an existing SensorCategory with no related Sensors
        WHEN: sending a DELETE request to the detail endpoint
        THEN: the SensorCategory is removed from the database
        """
        # GIVEN
        cat1, _ = obj
        count_before = SensorCategory.objects.count()
        url = self.get_url_detail(cat1)

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert SensorCategory.objects.count() == count_before - 1
        assert not SensorCategory.objects.filter(pk=cat1.pk).exists()

    def test_patch_not_allowed(self, authenticated_client, obj):
        """
        GIVEN: an existing SensorCategory
        WHEN: sending a PATCH request to the detail endpoint
        THEN: the response status is 405 Method Not Allowed
        """
        # GIVEN
        cat1, _ = obj
        url = self.get_url_detail(cat1)

        # WHEN
        response = authenticated_client.patch(url, {"name": "Partial"})

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ─── Sensor View Tests ────────────────────────────────────────────────────────


@pytest.mark.django_db
class SensorViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "sensors"
    MODEL = Sensor
    DATA_TO_DEFAULT_OBJ = {}

    @pytest.fixture
    def device_status(self, db):
        return Status.objects.create(name="Generic", tag="device-generic", color="#123456")

    @pytest.fixture
    def device(self, device_status):
        return Device.objects.create(
            name="Test Device",
            uid="AABBCCDDEEFF0011",
            path="/dev/ttyUSB0",
            status=device_status,
        )

    @pytest.fixture
    def channel(self, db):
        return Channel.objects.create(name="Analog")

    @pytest.fixture
    def pin(self, device, channel):
        p = Pin.objects.create(device=device, channel_choiced=channel, pin_number=1)
        p.channels_available.set([channel])
        return p

    @pytest.fixture
    def category(self, db):
        return SensorCategory.objects.create(name="Temperature", unity_value="°C", pin_init_cfg={})

    @pytest.fixture
    def obj(self, category, device, pin, channel):
        pin2 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        pin2.channels_available.set([channel])
        sensor1 = Sensor.objects.create(
            name="Sensor 1",
            category=category,
            device=device,
            pin=pin,
        )
        sensor2 = Sensor.objects.create(
            name="Sensor 2",
            category=category,
            device=device,
            pin=pin2,
        )
        return sensor1, sensor2


@pytest.mark.django_db
class TestSensorAPIModelView(SensorViewSetTestConf):

    def test_list(self, authenticated_client, obj):
        """
        GIVEN: two existing Sensors
        WHEN: sending a GET request to the list endpoint
        THEN: the response contains both sensors with minimal nested representation
        """
        # GIVEN
        sensor1, sensor2 = obj
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        names = [item["name"] for item in response.data["results"]]
        assert sensor1.name in names
        assert sensor2.name in names

        first = response.data["results"][0]
        assert "id" in first
        assert "name" in first
        assert isinstance(first["category"], dict)
        assert "id" in first["category"]
        assert "name" in first["category"]
        assert isinstance(first["device"], dict)
        assert "status" in first["device"]
        assert isinstance(first["pin"], dict)
        assert "pin_number" in first["pin"]
        assert "channel_choiced" in first["pin"]

    def test_retrieve(self, authenticated_client, obj):
        """
        GIVEN: an existing Sensor
        WHEN: sending a GET request to the detail endpoint
        THEN: the response contains the sensor with full device detail
        """
        # GIVEN
        sensor1, _ = obj
        url = self.get_url_detail(sensor1)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == sensor1.pk
        assert response.data["name"] == sensor1.name
        assert isinstance(response.data["category"], dict)
        assert "name" in response.data["category"]

        device_data = response.data["device"]
        assert isinstance(device_data, dict)
        assert "uid" in device_data
        assert "path" in device_data
        assert "last_seen" in device_data
        assert "gd_firmware_version" in device_data
        assert "mp_firmware_version" in device_data
        assert "need_upgrade" in device_data
        assert isinstance(device_data["status"], dict)

        assert isinstance(response.data["pin"], dict)
        assert "pin_number" in response.data["pin"]
        assert "channel_choiced" in response.data["pin"]

    def test_create(self, authenticated_client, category, device, pin):
        """
        GIVEN: a valid payload for a Sensor
        WHEN: sending a POST request to the create endpoint
        THEN: the Sensor is created and the response contains the correct PKs
        """
        # GIVEN
        payload = {
            "name": "New Sensor",
            "category": category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == payload["name"]
        assert response.data["category"] == category.pk
        assert response.data["device"] == device.pk
        assert response.data["pin"] == pin.pk
        assert Sensor.objects.filter(name=payload["name"]).exists()

    def test_update(self, authenticated_client, obj, category, device, pin):
        """
        GIVEN: an existing Sensor and updated data with new related objects
        WHEN: sending a PUT request to the detail endpoint
        THEN: the Sensor is updated with the new values
        """
        # GIVEN
        sensor1, _ = obj
        new_category = SensorCategory.objects.create(name="Humidity", unity_value="%", pin_init_cfg={})
        url = self.get_url_detail(sensor1)
        update_data = {
            "name": "Updated Sensor",
            "category": new_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        response = authenticated_client.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == update_data["name"]
        assert response.data["category"] == new_category.pk
        sensor1.refresh_from_db()
        assert sensor1.name == update_data["name"]
        assert sensor1.category == new_category

    def test_delete(self, authenticated_client, obj):
        """
        GIVEN: an existing Sensor
        WHEN: sending a DELETE request to the detail endpoint
        THEN: the Sensor is removed from the database
        """
        # GIVEN
        sensor1, _ = obj
        count_before = Sensor.objects.count()
        url = self.get_url_detail(sensor1)

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Sensor.objects.count() == count_before - 1
        assert not Sensor.objects.filter(pk=sensor1.pk).exists()

    def test_patch_not_allowed(self, authenticated_client, obj):
        """
        GIVEN: an existing Sensor
        WHEN: sending a PATCH request to the detail endpoint
        THEN: the response status is 405 Method Not Allowed
        """
        # GIVEN
        sensor1, _ = obj
        url = self.get_url_detail(sensor1)

        # WHEN
        response = authenticated_client.patch(url, {"name": "Partial"})

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
