import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory
from gardeniq.hardware.serializers import ControllerListReadOnlySerializer
from gardeniq.hardware.serializers import SensorListReadOnlySerializer
from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import OrderDetailReadOnlySerializer
from gardeniq.orderlg.serializers import OrderListReadOnlySerializer
from gardeniq.orderlg.serializers import OrderSeederSerializer
from gardeniq.orderlg.serializers import OrderSerializer

# ─── Hardware Fixtures ──────────────────────────────────────────────────────────


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
def pin2(device, channel):
    p = Pin.objects.create(
        device=device,
        channel_choiced=channel,
        pin_number=2,
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


@pytest.fixture
def controller_category(db):
    return ControllerCategory.objects.create(name="Relay")


@pytest.fixture
def controller(controller_category, device, pin2):
    return Controller.objects.create(
        name="Main Relay",
        category=controller_category,
        device=device,
        pin=pin2,
    )


# ─── Order Fixture ──────────────────────────────────────────────────────────────


@pytest.fixture
def create_order(sensor):
    """Create a getter Order with a sensor."""
    return Order.objects.create(
        name="Test Order",
        description="Test Order Description",
        action_type="get",
        sensor=sensor,
    )


# ─── TestOrderSerializer ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderSerializer:
    def test_valide_serializer(self, sensor):
        # GIVEN
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "get",
            "sensor": sensor.pk,
        }
        # Fields with allow_null=True (controller, ctrl_value) appear as None
        # even when not provided. Fields without allow_null (is_toggle_ctrl_value)
        # are absent from the output when not provided.
        # is_ready is read_only with default=True, so it appears in the output.
        expected = {
            "name": "Test Order",
            "description": "Test Order Description",
            "slug": "test-order",
            "action_type": "get",
            "is_enabled": True,
            "is_ready": True,
            "sensor": sensor.pk,
            "controller": None,
            "ctrl_value": None,
        }

        # WHEN
        serializer = OrderSerializer(data=data)

        # THEN
        assert serializer.is_valid()
        assert serializer.data == expected

    def test_validation_error_getter_without_sensor_and_controller(self):
        """
        GIVEN: a getter Order data without sensor and without controller
        WHEN: validating the serializer
        THEN: validation fails with a non_field_errors error
        """
        # GIVEN
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "get",
        }

        # WHEN
        serializer = OrderSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_validation_error_setter_without_controller(self):
        """
        GIVEN: a setter Order data without controller
        WHEN: validating the serializer
        THEN: validation fails with a non_field_errors error
        """
        # GIVEN
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "set",
        }

        # WHEN
        serializer = OrderSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_validation_error_setter_with_sensor(self, sensor, controller):
        """
        GIVEN: a setter Order data with both sensor and controller
        WHEN: validating the serializer
        THEN: validation fails because sensor must be empty for setter
        """
        # GIVEN
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "set",
            "sensor": sensor.pk,
            "controller": controller.pk,
        }

        # WHEN
        serializer = OrderSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_create_order(self, sensor):
        # GIVEN
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "get",
            "sensor": sensor.pk,
        }

        # WHEN
        serializer = OrderSerializer(data=data)
        assert serializer.is_valid()
        order = serializer.save()

        # THEN
        assert isinstance(order, Order)
        assert Order.objects.count() == 1
        assert order.name == data["name"]
        assert order.slug == "test-order"
        assert order.description == data["description"]
        assert order.action_type == data["action_type"]
        assert order.sensor == sensor
        assert order.controller is None

    def test_create_setter_order(self, controller):
        """
        GIVEN: valid setter Order data with a controller and ctrl_value
        WHEN: creating an Order via the serializer
        THEN: the Order is created with the correct setter fields
        """
        # GIVEN
        data = {
            "name": "Set LED On",
            "description": "Turn LED on",
            "action_type": "set",
            "controller": controller.pk,
            "ctrl_value": "1",
        }

        # WHEN
        serializer = OrderSerializer(data=data)
        assert serializer.is_valid()
        order = serializer.save()

        # THEN
        assert isinstance(order, Order)
        assert order.action_type == "set"
        assert order.controller == controller
        assert order.sensor is None
        assert order.ctrl_value == "1"

    def test_create_order_with_is_toggle_ctrl_value(self, controller):
        """
        GIVEN: setter Order data with is_toggle_ctrl_value=True
        WHEN: creating the Order via the serializer
        THEN: the is_toggle_ctrl_value field is stored correctly
        """
        # GIVEN
        data = {
            "name": "Toggle Relay",
            "description": "Toggle the relay state",
            "action_type": "set",
            "controller": controller.pk,
            "is_toggle_ctrl_value": True,
        }

        # WHEN
        serializer = OrderSerializer(data=data)
        assert serializer.is_valid()
        order = serializer.save()

        # THEN
        assert order.is_toggle_ctrl_value is True

    def test_create_order_with_custom_slug(self, sensor):
        # GIVEN
        data = {
            "name": "Test Order",
            "slug": "my-custom-slug-test-order",
            "description": "Test Order Description",
            "action_type": "get",
            "sensor": sensor.pk,
        }

        # WHEN
        serializer = OrderSerializer(data=data)
        assert serializer.is_valid()
        order = serializer.save()

        # THEN
        assert isinstance(order, Order)
        assert Order.objects.count() == 1
        assert order.name == data["name"]
        assert order.slug == data["slug"]
        assert order.description == data["description"]
        assert order.action_type == data["action_type"]

    def test_update_serializer(self, sensor):
        # GIVEN
        order = Order.objects.create(
            name="Test Update Order",
            description="Test Update Order Description",
            action_type="get",
            sensor=sensor,
        )
        updated_data = {
            "name": "New name for Test Update Order",
            "description": "New description for Test Update Order Description",
            "action_type": "get",
        }

        # WHEN
        serializer = OrderSerializer(instance=order, data=updated_data)
        assert serializer.is_valid()
        order = serializer.save()

        # THEN
        assert isinstance(order, Order)
        assert Order.objects.count() == 1
        assert order.name == updated_data["name"]
        assert order.slug == "new-name-for-test-update-order"
        assert order.description == updated_data["description"]
        assert order.action_type == updated_data["action_type"]
        assert order.sensor == sensor  # sensor unchanged

    def test_update_serializer_change_action_type_to_setter(self, sensor, controller):
        """
        GIVEN: an existing getter Order
        WHEN: updating it to a setter via the serializer (providing controller, removing sensor)
        THEN: the Order is updated correctly
        """
        # GIVEN
        order = Order.objects.create(
            name="Order To Update",
            description="Some description",
            action_type="get",
            sensor=sensor,
        )

        # WHEN
        updated_data = {
            "name": "Order To Update",
            "description": "Some description",
            "action_type": "set",
            "controller": controller.pk,
            "sensor": None,
        }
        serializer = OrderSerializer(instance=order, data=updated_data)
        assert serializer.is_valid()
        order = serializer.save()

        # THEN
        assert order.action_type == "set"
        assert order.controller == controller
        assert order.sensor is None


# ─── TestOrderListReadOnlySerializer ───────────────────────────────────────────


@pytest.mark.django_db
class TestOrderListReadOnlySerializer:
    def test_cannot_create_order_serializer(self):
        # GIVEN
        order_count_before = Order.objects.count()
        data = {
            "name": "Test Order",
            "action_type": "get",
        }

        # WHEN
        serializer = OrderListReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        order_count_after = Order.objects.count()

        # THEN
        assert order_count_before == order_count_after

    def test_cannot_update_order_serializer(self, create_order):
        # GIVEN
        order = create_order
        data = {
            "name": "Test Update Order",
            "action_type": "set",
        }

        # WHEN
        serializer = OrderListReadOnlySerializer(instance=order, data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        order_after_trying_update = Order.objects.get(pk=order.pk)

        # THEN
        assert order_after_trying_update.name != data["name"]
        assert order_after_trying_update.name == order.name

    def test_list_serializer(self, create_order, sensor):
        # GIVEN
        order = create_order
        expected = {
            "id": order.pk,
            "name": order.name,
            "slug": order.slug,
            "action_type": order.action_type,
            "is_enabled": order.is_enabled,
            "is_ready": order.is_ready,
            "sensor": sensor.name,
        }

        # WHEN
        serializer = OrderListReadOnlySerializer(instance=order)

        # THEN
        assert serializer.data == expected

    def test_list_serializer_setter_with_controller(self, controller):
        """
        GIVEN: a setter Order with a controller (no sensor)
        WHEN: serializing with OrderListReadOnlySerializer
        THEN: only the controller name appears (sensor field is absent)
        """
        # GIVEN
        order = Order.objects.create(
            name="Setter Order",
            action_type="set",
            controller=controller,
        )
        expected = {
            "id": order.pk,
            "name": order.name,
            "slug": order.slug,
            "action_type": order.action_type,
            "is_enabled": order.is_enabled,
            "is_ready": order.is_ready,
            "controller": controller.name,
        }

        # WHEN
        serializer = OrderListReadOnlySerializer(instance=order)

        # THEN
        assert serializer.data == expected

    def test_list_serializer_multiple_orders(self, sensor, controller):
        # GIVEN
        order1 = Order.objects.create(
            name="First Order",
            description="First Description",
            action_type="get",
            sensor=sensor,
        )
        order2 = Order.objects.create(
            name="Second Order",
            description="Second Description",
            action_type="set",
            controller=controller,
        )

        expected = [
            {
                "id": order1.pk,
                "name": order1.name,
                "slug": order1.slug,
                "action_type": order1.action_type,
                "is_enabled": order1.is_enabled,
                "is_ready": order1.is_ready,
                "sensor": sensor.name,
            },
            {
                "id": order2.pk,
                "name": order2.name,
                "slug": order2.slug,
                "action_type": order2.action_type,
                "is_enabled": order2.is_enabled,
                "is_ready": order2.is_ready,
                "controller": controller.name,
            },
        ]

        # WHEN
        serializer = OrderListReadOnlySerializer(instance=[order1, order2], many=True)

        # THEN
        assert serializer.data == expected


# ─── TestOrderDetailReadOnlySerializer ─────────────────────────────────────────


@pytest.mark.django_db
class TestOrderDetailReadOnlySerializer:
    def test_cannot_create_order_serializer(self):
        # GIVEN
        order_count_before = Order.objects.count()
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "get",
        }

        # WHEN
        serializer = OrderDetailReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        order_count_after = Order.objects.count()

        # THEN
        assert order_count_before == order_count_after

    def test_cannot_update_order_serializer(self, create_order):
        # GIVEN
        order = create_order
        data = {
            "name": "Test Update Order",
            "description": "Test Update Order Description",
            "action_type": "get",
        }

        # WHEN
        serializer = OrderDetailReadOnlySerializer(instance=order, data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        order_after_trying_update = Order.objects.get(pk=order.pk)

        # THEN
        assert order_after_trying_update.name != data["name"]
        assert order_after_trying_update.name == order.name

    def test_detail_serializer(self, create_order, sensor):
        # GIVEN
        order = create_order
        expected = {
            "id": order.pk,
            "name": order.name,
            "description": order.description,
            "slug": order.slug,
            "action_type": order.action_type,
            "is_enabled": order.is_enabled,
            "is_ready": order.is_ready,
            "sensor": SensorListReadOnlySerializer(instance=sensor).data,
            "controller": None,
            "is_toggle_ctrl_value": order.is_toggle_ctrl_value,
            "ctrl_value": order.ctrl_value,
        }

        # WHEN
        serializer = OrderDetailReadOnlySerializer(instance=order)

        # THEN
        assert serializer.data == expected

    def test_detail_serializer_setter_with_controller(self, controller):
        """
        GIVEN: a setter Order with a controller and ctrl_value
        WHEN: serializing with OrderDetailReadOnlySerializer
        THEN: all fields including nested controller and new fields are returned
        """
        # GIVEN
        order = Order.objects.create(
            name="Setter Order",
            description="Setter Description",
            action_type="set",
            controller=controller,
            ctrl_value="255",
        )
        expected = {
            "id": order.pk,
            "name": order.name,
            "description": order.description,
            "slug": order.slug,
            "action_type": order.action_type,
            "is_enabled": order.is_enabled,
            "is_ready": order.is_ready,
            "sensor": None,
            "controller": ControllerListReadOnlySerializer(instance=controller).data,
            "is_toggle_ctrl_value": order.is_toggle_ctrl_value,
            "ctrl_value": order.ctrl_value,
        }

        # WHEN
        serializer = OrderDetailReadOnlySerializer(instance=order)

        # THEN
        assert serializer.data == expected

    def test_detail_serializer_is_toggle_ctrl_value_true(self, controller):
        """
        GIVEN: a setter Order with is_toggle_ctrl_value=True
        WHEN: serializing with OrderDetailReadOnlySerializer
        THEN: is_toggle_ctrl_value is True in the response
        """
        # GIVEN
        order = Order.objects.create(
            name="Toggle Order",
            description="Toggle Description",
            action_type="set",
            controller=controller,
            is_toggle_ctrl_value=True,
        )

        # WHEN
        serializer = OrderDetailReadOnlySerializer(instance=order)

        # THEN
        assert serializer.data["is_toggle_ctrl_value"] is True
        assert serializer.data["ctrl_value"] is None

    def test_detail_serializer_ctrl_value(self, controller):
        """
        GIVEN: a setter Order with a specific ctrl_value
        WHEN: serializing with OrderDetailReadOnlySerializer
        THEN: ctrl_value is returned correctly
        """
        # GIVEN
        order = Order.objects.create(
            name="Ctrl Value Order",
            description="Ctrl Description",
            action_type="set",
            controller=controller,
            ctrl_value="128",
        )

        # WHEN
        serializer = OrderDetailReadOnlySerializer(instance=order)

        # THEN
        assert serializer.data["ctrl_value"] == "128"
        assert serializer.data["is_toggle_ctrl_value"] is False


# ─── TestOrderSeederSerializer ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderSeederSerializer:
    """Tests for OrderSeederSerializer."""

    def test_valid_seeder_serializer(self):
        """
        GIVEN: valid seeder data with seed_id > 0, is_ready=False, no sensor or controller
        WHEN: validating the OrderSeederSerializer
        THEN: validation passes
        """
        # GIVEN
        data = {
            "name": "Seeder Template",
            "description": "Template description",
            "action_type": "get",
            "seed_id": 1,
            "is_ready": False,
        }

        # WHEN
        serializer = OrderSeederSerializer(data=data)

        # THEN
        assert serializer.is_valid(), serializer.errors

    def test_create_seeder_order(self):
        """
        GIVEN: valid seeder data
        WHEN: creating an Order via OrderSeederSerializer
        THEN: the Order is created with seed_id, is_ready=False, and no sensor or controller
        """
        # GIVEN
        data = {
            "name": "Seeder Template",
            "description": "Template description",
            "action_type": "get",
            "seed_id": 1,
            "is_ready": False,
        }

        # WHEN
        serializer = OrderSeederSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        # THEN
        assert isinstance(order, Order)
        assert order.seed_id == 1
        assert order.is_ready is False
        assert order.sensor is None
        assert order.controller is None
        assert order.name == data["name"]
        assert order.slug == "seeder-template"

    def test_create_seeder_order_with_custom_slug(self):
        """
        GIVEN: valid seeder data with a custom slug
        WHEN: creating an Order via OrderSeederSerializer
        THEN: the custom slug is used
        """
        # GIVEN
        data = {
            "name": "Seeder Template",
            "description": "Template description",
            "action_type": "get",
            "seed_id": 1,
            "is_ready": False,
            "slug": "my-custom-seeder-slug",
        }

        # WHEN
        serializer = OrderSeederSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        # THEN
        assert order.slug == "my-custom-seeder-slug"

    def test_validation_error_missing_seed_id(self):
        """
        GIVEN: seeder data without seed_id
        WHEN: validating the OrderSeederSerializer
        THEN: validation fails on the seed_id field
        """
        # GIVEN
        data = {
            "name": "Seeder Template",
            "description": "Template description",
            "action_type": "get",
            "is_ready": False,
        }

        # WHEN
        serializer = OrderSeederSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "seed_id" in serializer.errors

    def test_validation_error_is_ready_true(self):
        """
        GIVEN: seeder data with is_ready=True
        WHEN: validating the OrderSeederSerializer
        THEN: validation fails (seeder template must have is_ready=False)
        """
        # GIVEN
        data = {
            "name": "Seeder Template",
            "description": "Template description",
            "action_type": "get",
            "seed_id": 1,
            "is_ready": True,
        }

        # WHEN
        serializer = OrderSeederSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_validation_error_with_sensor(self, sensor):
        """
        GIVEN: seeder data with a sensor
        WHEN: validating the OrderSeederSerializer
        THEN: validation fails (seeder template must not have a sensor)
        """
        # GIVEN
        data = {
            "name": "Seeder Template",
            "description": "Template description",
            "action_type": "get",
            "seed_id": 1,
            "is_ready": False,
            "sensor": sensor.pk,
        }

        # WHEN
        serializer = OrderSeederSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_validation_error_with_controller(self, controller):
        """
        GIVEN: seeder data with a controller
        WHEN: validating the OrderSeederSerializer
        THEN: validation fails (seeder template must not have a controller)
        """
        # GIVEN
        data = {
            "name": "Seeder Template",
            "description": "Template description",
            "action_type": "set",
            "seed_id": 1,
            "is_ready": False,
            "controller": controller.pk,
        }

        # WHEN
        serializer = OrderSeederSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_update_seeder_order(self):
        """
        GIVEN: an existing seeder Order
        WHEN: updating it via OrderSeederSerializer
        THEN: the Order is updated with the new values
        """
        # GIVEN
        order = Order.objects.create(
            name="Old Seeder Template",
            description="Old description",
            action_type="get",
            seed_id=5,
            is_ready=False,
        )
        updated_data = {
            "name": "Updated Seeder Template",
            "description": "Updated description",
            "action_type": "get",
            "seed_id": 5,
            "is_ready": False,
        }

        # WHEN
        serializer = OrderSeederSerializer(instance=order, data=updated_data)
        assert serializer.is_valid(), serializer.errors
        updated_order = serializer.save()

        # THEN
        assert updated_order.name == updated_data["name"]
        assert updated_order.description == updated_data["description"]
        assert updated_order.slug == "updated-seeder-template"
        assert updated_order.seed_id == 5
        assert updated_order.is_ready is False
