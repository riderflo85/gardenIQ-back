from rest_framework import status

import pytest

from gardeniq.base.models import Status
from gardeniq.base.utils.tests import ViewSetTestMixin
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.models import Pin

VALID_PIN_INIT_CFG = {"c": "Pin", "a": {"id": "@pin"}}

# ─── ControllerCategory View Tests ────────────────────────────────────────────


@pytest.mark.django_db
class ControllerCategoryViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "controller-categories"
    MODEL = ControllerCategory
    DATA_TO_DEFAULT_OBJ = {"name": "Default Category", "pin_init_cfg": VALID_PIN_INIT_CFG}

    def generate_default_obj(self):
        cat1 = ControllerCategory.objects.create(name="Relay", pin_init_cfg=VALID_PIN_INIT_CFG)
        cat2 = ControllerCategory.objects.create(name="LED Driver", pin_init_cfg=VALID_PIN_INIT_CFG)
        return cat1, cat2


@pytest.mark.django_db
class TestControllerCategoryAPIModelView(ControllerCategoryViewSetTestConf):

    def test_list(self, authenticated_client, obj):
        """Test retrieving the list of controller categories."""
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
        assert "pin_init_cfg" not in first
        assert first["is_ready"] is True

    def test_retrieve(self, authenticated_client, obj):
        """Test retrieving a specific controller category."""
        # GIVEN
        cat1, _ = obj
        url = self.get_url_detail(cat1)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == cat1.pk
        assert response.data["name"] == cat1.name
        assert response.data["pin_init_cfg"] == cat1.pin_init_cfg
        assert response.data["is_ready"] is True

    def test_create(self, authenticated_client):
        """Test creating a new controller category."""
        # GIVEN
        payload = {"name": "New Category", "pin_init_cfg": VALID_PIN_INIT_CFG}
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == payload["name"]
        assert response.data["pin_init_cfg"] == payload["pin_init_cfg"]
        assert ControllerCategory.objects.filter(name=payload["name"]).exists()

    def test_update(self, authenticated_client, obj):
        """Test updating an existing controller category."""
        # GIVEN
        cat1, _ = obj
        url = self.get_url_detail(cat1)
        update_data = {"name": "Updated Relay", "pin_init_cfg": {"c": "PWM", "a": {"dest": "@pin", "freq": 500}}}

        # WHEN
        response = authenticated_client.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == update_data["name"]
        assert response.data["pin_init_cfg"] == update_data["pin_init_cfg"]
        cat1.refresh_from_db()
        assert cat1.name == update_data["name"]
        assert cat1.pin_init_cfg == update_data["pin_init_cfg"]

    def test_create_with_invalid_pin_init_cfg(self, authenticated_client):
        """Test that creating a controller category with an invalid pin_init_cfg returns 400."""
        # GIVEN
        payload = {"name": "New Category", "pin_init_cfg": {"c": "Pin", "a": {"id": 4}}}
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.content
        assert "pin_init_cfg" in response.data["errors"]
        assert response.data["errors"]["pin_init_cfg"][0].startswith("Failed validation JSON schema")
        assert not ControllerCategory.objects.filter(name=payload["name"]).exists()

    def test_update_with_invalid_pin_init_cfg(self, authenticated_client, obj):
        """Test that updating a controller category with an invalid pin_init_cfg returns 400 and keeps the old value."""
        # GIVEN
        cat1, _ = obj
        url = self.get_url_detail(cat1)
        update_data = {"name": "New Category", "pin_init_cfg": {"c": "UART", "a": {"id": "@pin"}}}

        # WHEN
        response = authenticated_client.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.content
        assert "pin_init_cfg" in response.data["errors"]
        cat1.refresh_from_db()
        assert cat1.pin_init_cfg == VALID_PIN_INIT_CFG

    def test_delete(self, authenticated_client, obj):
        """Test deleting a controller category."""
        # GIVEN
        cat1, _ = obj
        count_before = ControllerCategory.objects.count()
        url = self.get_url_detail(cat1)

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert ControllerCategory.objects.count() == count_before - 1
        assert not ControllerCategory.objects.filter(pk=cat1.pk).exists()

    def test_patch_not_allowed(self, authenticated_client, obj):
        """Test that PATCH method is not allowed."""
        # GIVEN
        cat1, _ = obj
        url = self.get_url_detail(cat1)

        # WHEN
        response = authenticated_client.patch(url, {"name": "Partial"})

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ─── Controller View Tests ─────────────────────────────────────────────────────


@pytest.mark.django_db
class ControllerViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "controllers"
    MODEL = Controller
    DATA_TO_DEFAULT_OBJ = {}

    @pytest.fixture
    def device_status(self, db):
        return Status.objects.create(name="Generic", tag="device-generic", color="#123456")

    @pytest.fixture
    def device_category(self):
        return DeviceCategory.objects.create(
            name="Test Category",
            pins_configuration={"available_channels": [], "digits": [], "pwms": [], "analogs": []},
        )

    @pytest.fixture
    def device(self, device_status, device_category):
        return Device.objects.create(
            name="Test Device",
            uid="AABBCCDDEEFF0011",
            path="/dev/ttyUSB0",
            status=device_status,
            category=device_category,
        )

    @pytest.fixture
    def channel(self, db):
        return Channel.objects.create(name="Digital")

    @pytest.fixture
    def pin(self, device, channel):
        p = Pin.objects.create(device=device, channel_choiced=channel, pin_number=1)
        p.channels_available.set([channel])
        return p

    @pytest.fixture
    def category(self, db):
        return ControllerCategory.objects.create(name="Relay", pin_init_cfg=VALID_PIN_INIT_CFG)

    @pytest.fixture
    def obj(self, category, device, pin, channel):
        pin2 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        pin2.channels_available.set([channel])
        ctrl1 = Controller.objects.create(
            name="Controller 1",
            category=category,
            pin=pin,
        )
        ctrl2 = Controller.objects.create(
            name="Controller 2",
            category=category,
            pin=pin2,
        )
        return ctrl1, ctrl2


@pytest.mark.django_db
class TestControllerAPIModelView(ControllerViewSetTestConf):

    def test_list(self, authenticated_client, obj):
        """Test retrieving the list of controllers with minimal nested representation."""
        # GIVEN
        ctrl1, ctrl2 = obj
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        names = [item["name"] for item in response.data["results"]]
        assert ctrl1.name in names
        assert ctrl2.name in names

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
        """Test retrieving a specific controller with full device detail."""
        # GIVEN
        ctrl1, _ = obj
        url = self.get_url_detail(ctrl1)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == ctrl1.pk
        assert response.data["name"] == ctrl1.name
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
        """Test creating a new controller."""
        # GIVEN
        payload = {
            "name": "New Controller",
            "category": category.pk,
            "pin": pin.pk,
        }
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == payload["name"]
        assert response.data["category"] == category.pk
        assert response.data["pin"] == pin.pk
        assert Controller.objects.filter(name=payload["name"]).exists()

    def test_update(self, authenticated_client, obj, category, device, pin):
        """Test updating an existing controller."""
        # GIVEN
        ctrl1, _ = obj
        new_category = ControllerCategory.objects.create(name="Motor Controller", pin_init_cfg=VALID_PIN_INIT_CFG)
        url = self.get_url_detail(ctrl1)
        update_data = {
            "name": "Updated Controller",
            "category": new_category.pk,
            "pin": pin.pk,
        }

        # WHEN
        response = authenticated_client.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == update_data["name"]
        assert response.data["category"] == new_category.pk
        ctrl1.refresh_from_db()
        assert ctrl1.name == update_data["name"]
        assert ctrl1.category == new_category

    def test_delete(self, authenticated_client, obj):
        """Test deleting a controller."""
        # GIVEN
        ctrl1, _ = obj
        count_before = Controller.objects.count()
        url = self.get_url_detail(ctrl1)

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Controller.objects.count() == count_before - 1
        assert not Controller.objects.filter(pk=ctrl1.pk).exists()

    def test_patch_not_allowed(self, authenticated_client, obj):
        """Test that PATCH method is not allowed."""
        # GIVEN
        ctrl1, _ = obj
        url = self.get_url_detail(ctrl1)

        # WHEN
        response = authenticated_client.patch(url, {"name": "Partial"})

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestControllerAPIModelViewPin(ControllerViewSetTestConf):

    def test_create_with_used_pin_returns_400(self, authenticated_client, obj, category):
        """
        GIVEN: a Pin already used by a Controller
        WHEN: sending a POST request with the same Pin
        THEN: the response is 400 with an error on pin
        """
        # GIVEN
        first, _ = obj
        payload = {"name": "Duplicate", "category": category.pk, "pin": first.pin.pk}

        # WHEN
        response = authenticated_client.post(self.get_url_create(), payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.content
        assert list(response.data["errors"]) == ["pin"]

    def test_list_filters_by_device(self, authenticated_client, obj, category, device_status, device_category, channel):
        """
        GIVEN: two Controllers on a device and one on another device
        WHEN: listing with ?device=<other device>
        THEN: only the Controller of the other device is returned
        """
        # GIVEN
        other_device = Device.objects.create(
            name="Other Device",
            uid="1122334455667788",
            path="/dev/ttyUSB1",
            status=device_status,
            category=device_category,
        )
        other_pin = Pin.objects.create(device=other_device, channel_choiced=channel, pin_number=1)
        other = Controller.objects.create(name="Other", category=category, pin=other_pin)

        # WHEN
        response = authenticated_client.get(self.get_url_list(), {"device": other_device.pk})

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert [item["id"] for item in response.data["results"]] == [other.pk]

    def test_list_filters_by_category(self, authenticated_client, obj, category):
        """
        GIVEN: two Controllers, one moved to a new category
        WHEN: listing with ?category=<new category>
        THEN: only that Controller is returned
        """
        # GIVEN
        first, _ = obj
        new_category = ControllerCategory.objects.create(name="New", pin_init_cfg=VALID_PIN_INIT_CFG)
        first.category = new_category
        first.save()

        # WHEN
        response = authenticated_client.get(self.get_url_list(), {"category": new_category.pk})

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert [item["id"] for item in response.data["results"]] == [first.pk]
