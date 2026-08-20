from rest_framework import status

import pytest

from gardeniq.base.models import Status
from gardeniq.base.utils.tests import ViewSetTestMixin
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory
from gardeniq.orderlg.models import Order

# ─── Order View Tests ──────────────────────────────────────────────────────────


@pytest.mark.django_db
class OrderViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "orders"
    MODEL = Order
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
    def pin2(self, device, channel):
        p = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        p.channels_available.set([channel])
        return p

    @pytest.fixture
    def sensor_category(self, db):
        return SensorCategory.objects.create(name="Temperature", unity_value="°C")

    @pytest.fixture
    def sensor(self, sensor_category, device, pin):
        return Sensor.objects.create(
            name="Main Temp Sensor",
            category=sensor_category,
            device=device,
            pin=pin,
        )

    @pytest.fixture
    def controller_category(self, db):
        return ControllerCategory.objects.create(name="Relay")

    @pytest.fixture
    def controller(self, controller_category, device, pin2):
        return Controller.objects.create(
            name="Main Relay",
            category=controller_category,
            device=device,
            pin=pin2,
        )

    @pytest.fixture
    def obj(self, sensor, controller):
        """Create one getter Order (with sensor) and one setter Order (with controller)."""
        order1 = Order.objects.create(
            name="Test Order 1",
            description="First test order",
            action_type="get",
            sensor=sensor,
        )
        order2 = Order.objects.create(
            name="Test Order 2",
            description="Second test order",
            action_type="set",
            controller=controller,
        )
        return order1, order2


@pytest.mark.django_db
class TestOrderAPIModelView(OrderViewSetTestConf):

    def test_list(self, authenticated_client, obj):
        """
        GIVEN: a getter Order and a setter Order in the database
        WHEN: sending a GET request to the list endpoint
        THEN: the response contains both orders with the expected list fields
        """
        # GIVEN
        order1, order2 = obj
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        names = [order["name"] for order in response.data["results"]]
        assert order1.name in names
        assert order2.name in names

        first_order = response.data["results"][0]
        assert "id" in first_order
        assert "name" in first_order
        assert "slug" in first_order
        assert "action_type" in first_order
        assert "is_enabled" in first_order
        assert "is_ready" in first_order

    def test_retrieve(self, authenticated_client, obj):
        """
        GIVEN: an existing getter Order with a sensor
        WHEN: sending a GET request to the detail endpoint
        THEN: the response contains the full Order detail including new fields
        """
        # GIVEN
        order1, _ = obj
        url = self.get_url_detail(order1.pk)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == order1.pk
        assert response.data["name"] == order1.name
        assert response.data["description"] == order1.description
        assert response.data["action_type"] == order1.action_type
        assert isinstance(response.data["sensor"], dict)
        assert "name" in response.data["sensor"]
        assert response.data["controller"] is None
        assert "is_toggle_ctrl_value" in response.data
        assert "ctrl_value" in response.data
        assert response.data["is_ready"] is True

    def test_retrieve_setter_order(self, authenticated_client, obj):
        """
        GIVEN: an existing setter Order with a controller
        WHEN: sending a GET request to the detail endpoint
        THEN: the response contains the full Order detail with controller and null sensor
        """
        # GIVEN
        _, order2 = obj
        url = self.get_url_detail(order2.pk)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["action_type"] == "set"
        assert response.data["sensor"] is None
        assert isinstance(response.data["controller"], dict)
        assert "name" in response.data["controller"]
        assert "is_toggle_ctrl_value" in response.data
        assert "ctrl_value" in response.data
        assert response.data["is_ready"] is True

    def test_create(self, authenticated_client, sensor):
        """
        GIVEN: a valid payload for a getter Order with a sensor
        WHEN: sending a POST request to the create endpoint
        THEN: the Order is created and the response contains the correct data
        """
        # GIVEN
        payload = {
            "name": "New Order",
            "description": "A new test order",
            "action_type": "get",
            "sensor": sensor.pk,
        }
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == payload["name"]
        assert response.data["description"] == payload["description"]
        assert response.data["action_type"] == payload["action_type"]
        assert response.data["sensor"] == sensor.pk
        assert response.data["controller"] is None
        assert response.data["is_ready"] is True
        assert Order.objects.filter(name=payload["name"]).exists()

    def test_create_setter_order(self, authenticated_client, controller):
        """
        GIVEN: a valid payload for a setter Order with a controller and a ctrl_value
        WHEN: sending a POST request to the create endpoint
        THEN: the setter Order is created and the response contains the correct data
        """
        # GIVEN
        payload = {
            "name": "Set LED On",
            "description": "Turn LED on",
            "action_type": "set",
            "controller": controller.pk,
            "ctrl_value": "1",
        }
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["action_type"] == "set"
        assert response.data["controller"] == controller.pk
        assert response.data["sensor"] is None
        assert response.data["ctrl_value"] == "1"
        assert response.data["is_ready"] is True
        assert Order.objects.filter(name=payload["name"]).exists()

    def test_create_with_invalid_constraint_getter_no_sensor_controller(self, authenticated_client):
        """
        GIVEN: a getter Order payload without sensor and without controller
        WHEN: sending a POST request to the create endpoint
        THEN: the response is 400 Bad Request
        """
        # GIVEN
        payload = {
            "name": "Bad Getter",
            "description": "Missing sensor or controller",
            "action_type": "get",
        }
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_with_invalid_constraint_setter_no_controller(self, authenticated_client):
        """
        GIVEN: a setter Order payload without a controller
        WHEN: sending a POST request to the create endpoint
        THEN: the response is 400 Bad Request
        """
        # GIVEN
        payload = {
            "name": "Bad Setter",
            "description": "Missing controller",
            "action_type": "set",
        }
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update(self, authenticated_client, obj, controller):
        """
        GIVEN: an existing getter Order
        WHEN: sending a PUT request to update it to a setter with a controller
        THEN: the Order is updated correctly in the response and in the database
        """
        # GIVEN
        order1, _ = obj
        url = self.get_url_detail(order1.pk)
        update_data = {
            "name": "Updated Order",
            "description": "Updated description",
            "action_type": "set",
            "controller": controller.pk,
            "sensor": None,
        }

        # WHEN
        response = authenticated_client.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == update_data["name"]
        assert response.data["description"] == update_data["description"]
        assert response.data["action_type"] == update_data["action_type"]
        assert response.data["controller"] == controller.pk
        assert response.data["sensor"] is None
        assert response.data["is_ready"] is True

        order1.refresh_from_db()
        assert order1.name == update_data["name"]
        assert order1.action_type == update_data["action_type"]
        assert order1.controller == controller
        assert order1.sensor is None

    def test_delete(self, authenticated_client, obj):
        """
        GIVEN: an existing Order
        WHEN: sending a DELETE request to the detail endpoint
        THEN: the Order is removed from the database
        """
        # GIVEN
        order1, _ = obj
        count_before = Order.objects.count()
        url = self.get_url_detail(order1.pk)

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Order.objects.count() == count_before - 1
        assert not Order.objects.filter(pk=order1.pk).exists()

    def test_patch_not_allowed(self, authenticated_client, obj):
        """
        GIVEN: an existing Order
        WHEN: sending a PATCH request to the detail endpoint
        THEN: the response status is 405 Method Not Allowed
        """
        # GIVEN
        order1, _ = obj
        url = self.get_url_detail(order1.pk)

        # WHEN
        response = authenticated_client.patch(url, {"name": "Partial"})

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
