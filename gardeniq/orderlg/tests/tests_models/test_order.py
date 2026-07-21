from django.db import IntegrityError

import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory
from gardeniq.orderlg.models import Order

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


# ─── Order Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def order_data(sensor):
    """Fixture providing basic data to create a getter Order."""
    return {
        "name": "Get Temperature",
        "description": "Retrieve temperature from sensor",
        "slug": "get-temperature",
        "action_type": "get",
        "sensor": sensor,
    }


@pytest.fixture
def order_setter_data(controller):
    """Fixture providing data for a setter Order."""
    return {
        "name": "Set LED State",
        "description": "Set the state of the LED",
        "slug": "set-led-state",
        "action_type": "set",
        "controller": controller,
    }


@pytest.fixture
def order_minimal_data(sensor):
    """Fixture providing minimal data relying on defaults."""
    return {
        "name": "Check Status",
        "action_type": "get",
        "sensor": sensor,
    }


# ─── TestOrderCreation ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderCreation:
    """Tests for Order model creation."""

    def test_create_order_with_all_fields(self, order_data):
        """
        GIVEN: complete data for a getter Order
        WHEN: creating an Order with all fields
        THEN: the Order is created with correct values
        """
        # GIVEN - data is provided by the order_data fixture

        # WHEN
        order = Order.objects.create(**order_data)

        # THEN
        assert order.pk is not None
        assert order.name == order_data["name"]
        assert order.description == order_data["description"]
        assert order.slug == order_data["slug"]
        assert order.action_type == order_data["action_type"]
        assert order.sensor == order_data["sensor"]
        assert order.is_enabled is True  # from ProtectedDisabledMixinModel

    def test_create_order_with_minimal_data(self, order_minimal_data):
        """
        GIVEN: minimal data for a getter Order
        WHEN: creating an Order with minimal data
        THEN: the Order is created with default values
        """
        # GIVEN - data is provided by the fixture

        # WHEN
        order = Order.objects.create(**order_minimal_data)

        # THEN
        assert order.pk is not None
        assert order.name == order_minimal_data["name"]
        assert order.action_type == order_minimal_data["action_type"]
        assert order.is_enabled is True

    def test_create_order_with_getter_action(self, order_data):
        """
        GIVEN: data for a getter Order
        WHEN: creating an Order with action_type='get'
        THEN: the Order is created as a getter
        """
        # GIVEN - data is provided by the fixture

        # WHEN
        order = Order.objects.create(**order_data)

        # THEN
        assert order.pk is not None
        assert order.action_type == "get"

    def test_create_order_with_setter_action(self, order_setter_data):
        """
        GIVEN: data for a setter Order
        WHEN: creating an Order with action_type='set'
        THEN: the Order is created as a setter
        """
        # GIVEN - data is provided by the fixture

        # WHEN
        order = Order.objects.create(**order_setter_data)

        # THEN
        assert order.pk is not None
        assert order.action_type == "set"


# ─── TestOrderStringRepresentation ─────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderStringRepresentation:
    """Tests for Order model string representation."""

    def test_str_method_returns_correct_format_when_enabled(self, order_data):
        """
        GIVEN: a created enabled Order
        WHEN: calling the __str__ method
        THEN: it returns the format "Order `{name}` enabled"
        """
        # GIVEN
        order = Order.objects.create(**order_data)

        # WHEN
        result = str(order)

        # THEN
        expected = f"Order `{order_data['name']}` enabled"
        assert result == expected

    def test_str_method_returns_correct_format_when_disabled(self, order_data):
        """
        GIVEN: a created disabled Order
        WHEN: calling the __str__ method
        THEN: it returns the format "Order `{name}` disabled"
        """
        # GIVEN
        order_data["is_enabled"] = False
        order = Order.objects.create(**order_data)

        # WHEN
        result = str(order)

        # THEN
        expected = f"Order `{order_data['name']}` disabled"
        assert result == expected


# ─── TestOrderFields ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderFields:
    """Tests for Order model fields and constraints."""

    def test_name_field(self, sensor):
        """
        GIVEN: a name for an Order
        WHEN: creating an Order with this name
        THEN: the Order is created with the correct name
        """
        # GIVEN
        name = "Get Sensor Data"

        # WHEN
        order = Order.objects.create(
            name=name,
            action_type="get",
            sensor=sensor,
        )

        # THEN
        assert order.name == name

    def test_description_field(self, sensor):
        """
        GIVEN: a description for an Order
        WHEN: creating an Order with this description
        THEN: the Order is created with the correct description
        """
        # GIVEN
        long_description = "A" * 500

        # WHEN
        order = Order.objects.create(
            name="Test Order",
            description=long_description,
            action_type="get",
            sensor=sensor,
        )

        # THEN
        assert order.description == long_description

    def test_slug_field(self, sensor):
        """
        GIVEN: a valid slug
        WHEN: creating an Order with this slug
        THEN: the Order is created with the correct slug
        """
        # GIVEN
        slug = "get-temperature-sensor-external"

        # WHEN
        order = Order.objects.create(
            name="Get Temperature Sensor External",
            slug=slug,
            action_type="get",
            sensor=sensor,
        )

        # THEN
        assert order.slug == slug

    def test_action_type_field_getter(self, sensor):
        """
        GIVEN: action_type='get' and a sensor
        WHEN: creating an Order with getter action
        THEN: the action_type field is set to 'get'
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Getter Order",
            action_type="get",
            sensor=sensor,
        )

        # THEN
        assert order.action_type == "get"

    def test_action_type_field_setter(self, controller):
        """
        GIVEN: action_type='set' and a controller
        WHEN: creating an Order with setter action
        THEN: the action_type field is set to 'set'
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Setter Order",
            action_type="set",
            controller=controller,
        )

        # THEN
        assert order.action_type == "set"

    def test_is_enabled_field_default_is_true(self, sensor):
        """
        GIVEN: data without specifying is_enabled field
        WHEN: creating an Order
        THEN: the is_enabled field defaults to True
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Test Order",
            action_type="get",
            sensor=sensor,
        )

        # THEN
        assert order.is_enabled is True

    def test_is_toggle_ctrl_value_default_is_false(self, controller):
        """
        GIVEN: data without specifying is_toggle_ctrl_value
        WHEN: creating a setter Order
        THEN: the is_toggle_ctrl_value field defaults to False
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Setter Order",
            action_type="set",
            controller=controller,
        )

        # THEN
        assert order.is_toggle_ctrl_value is False

    def test_is_toggle_ctrl_value_can_be_true(self, controller):
        """
        GIVEN: is_toggle_ctrl_value=True
        WHEN: creating a setter Order
        THEN: the is_toggle_ctrl_value field is set to True
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Toggle Order",
            action_type="set",
            controller=controller,
            is_toggle_ctrl_value=True,
        )

        # THEN
        assert order.is_toggle_ctrl_value is True

    def test_ctrl_value_default_is_null(self, controller):
        """
        GIVEN: data without specifying ctrl_value
        WHEN: creating a setter Order
        THEN: the ctrl_value field defaults to None
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Setter Order",
            action_type="set",
            controller=controller,
        )

        # THEN
        assert order.ctrl_value is None

    def test_ctrl_value_can_be_set(self, controller):
        """
        GIVEN: ctrl_value='1'
        WHEN: creating a setter Order with a ctrl_value
        THEN: the ctrl_value field is set correctly
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Ctrl Order",
            action_type="set",
            controller=controller,
            ctrl_value="1",
        )

        # THEN
        assert order.ctrl_value == "1"

    def test_ctrl_value_can_be_blank(self, controller):
        """
        GIVEN: ctrl_value=''
        WHEN: creating a setter Order with an empty ctrl_value
        THEN: the ctrl_value field stores an empty string
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Empty Ctrl Order",
            action_type="set",
            controller=controller,
            ctrl_value="",
        )

        # THEN
        assert order.ctrl_value == ""

    def test_sensor_field_is_none_for_setter(self, controller):
        """
        GIVEN: a setter Order created without sensor
        WHEN: reading the sensor field
        THEN: the sensor field is None
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Setter No Sensor",
            action_type="set",
            controller=controller,
        )

        # THEN
        assert order.sensor is None

    def test_controller_field_is_none_for_getter_with_sensor_only(self, sensor):
        """
        GIVEN: a getter Order created with only a sensor
        WHEN: reading the controller field
        THEN: the controller field is None
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Getter No Controller",
            action_type="get",
            sensor=sensor,
        )

        # THEN
        assert order.controller is None


# ─── TestOrderConstraints ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderConstraints:
    """Tests for the check_order_action_type_sensor_controller constraint."""

    def test_getter_without_sensor_and_controller_raises_integrity_error(self):
        """
        GIVEN: action_type='get' without sensor and without controller
        WHEN: creating the Order
        THEN: an IntegrityError is raised
        """
        # GIVEN / WHEN / THEN
        with pytest.raises(IntegrityError):
            Order.objects.create(name="Bad Getter", action_type="get")

    def test_setter_without_controller_raises_integrity_error(self):
        """
        GIVEN: action_type='set' without controller
        WHEN: creating the Order
        THEN: an IntegrityError is raised
        """
        # GIVEN / WHEN / THEN
        with pytest.raises(IntegrityError):
            Order.objects.create(name="Bad Setter", action_type="set")

    def test_setter_with_sensor_raises_integrity_error(self, sensor, controller):
        """
        GIVEN: action_type='set' with both a sensor and a controller
        WHEN: creating the Order
        THEN: an IntegrityError is raised (sensor must be null for setter)
        """
        # GIVEN / WHEN / THEN
        with pytest.raises(IntegrityError):
            Order.objects.create(
                name="Setter With Sensor",
                action_type="set",
                sensor=sensor,
                controller=controller,
            )

    def test_getter_with_sensor_only_is_valid(self, sensor):
        """
        GIVEN: action_type='get' with a sensor (no controller)
        WHEN: creating the Order
        THEN: the Order is created successfully
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Getter Sensor Only",
            action_type="get",
            sensor=sensor,
        )

        # THEN
        assert order.pk is not None

    def test_getter_with_controller_only_is_valid(self, controller):
        """
        GIVEN: action_type='get' with a controller (no sensor)
        WHEN: creating the Order
        THEN: the Order is created successfully
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Getter Controller Only",
            action_type="get",
            controller=controller,
        )

        # THEN
        assert order.pk is not None

    def test_getter_with_sensor_and_controller_is_valid(self, sensor, controller):
        """
        GIVEN: action_type='get' with both a sensor and a controller
        WHEN: creating the Order
        THEN: the Order is created successfully
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Getter Both",
            action_type="get",
            sensor=sensor,
            controller=controller,
        )

        # THEN
        assert order.pk is not None

    def test_setter_with_controller_only_is_valid(self, controller):
        """
        GIVEN: action_type='set' with a controller (no sensor)
        WHEN: creating the Order
        THEN: the Order is created successfully
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Setter Controller Only",
            action_type="set",
            controller=controller,
        )

        # THEN
        assert order.pk is not None


# ─── TestOrderUpdate ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderUpdate:
    """Tests for Order model update operations."""

    def test_update_order_name(self, order_data):
        """
        GIVEN: an existing Order
        WHEN: updating its name
        THEN: the name is modified correctly
        """
        # GIVEN
        order = Order.objects.create(**order_data)
        new_name = "Updated Order Name"

        # WHEN
        order.name = new_name
        order.save()

        # THEN
        updated_order = Order.objects.get(pk=order.pk)
        assert updated_order.name == new_name

    def test_update_order_description(self, order_data):
        """
        GIVEN: an existing Order
        WHEN: updating its description
        THEN: the description is modified correctly
        """
        # GIVEN
        order = Order.objects.create(**order_data)
        new_description = "Updated description"

        # WHEN
        order.description = new_description
        order.save()

        # THEN
        updated_order = Order.objects.get(pk=order.pk)
        assert updated_order.description == new_description

    def test_update_order_action_type_from_getter_to_setter(self, order_data, controller):
        """
        GIVEN: an existing getter Order
        WHEN: updating its action_type to 'set', assigning a controller and removing the sensor
        THEN: the action_type and related fields are updated correctly
        """
        # GIVEN
        order = Order.objects.create(**order_data)
        assert order.action_type == "get"

        # WHEN
        order.action_type = "set"
        order.sensor = None
        order.controller = controller
        order.save()

        # THEN
        updated_order = Order.objects.get(pk=order.pk)
        assert updated_order.action_type == "set"
        assert updated_order.sensor is None
        assert updated_order.controller == controller

    def test_update_order_enabled_status(self, order_data):
        """
        GIVEN: an existing enabled Order
        WHEN: disabling the Order
        THEN: the is_enabled field is modified correctly
        """
        # GIVEN
        order = Order.objects.create(**order_data)
        assert order.is_enabled is True

        # WHEN
        order.is_enabled = False
        order.save()

        # THEN
        updated_order = Order.objects.get(pk=order.pk)
        assert updated_order.is_enabled is False

    def test_update_ctrl_value(self, order_setter_data):
        """
        GIVEN: an existing setter Order with ctrl_value=None
        WHEN: updating its ctrl_value
        THEN: the ctrl_value is modified correctly
        """
        # GIVEN
        order = Order.objects.create(**order_setter_data)
        assert order.ctrl_value is None

        # WHEN
        order.ctrl_value = "255"
        order.save()

        # THEN
        updated_order = Order.objects.get(pk=order.pk)
        assert updated_order.ctrl_value == "255"

    def test_update_is_toggle_ctrl_value(self, order_setter_data):
        """
        GIVEN: an existing setter Order with is_toggle_ctrl_value=False
        WHEN: updating its is_toggle_ctrl_value to True
        THEN: the is_toggle_ctrl_value is modified correctly
        """
        # GIVEN
        order = Order.objects.create(**order_setter_data)
        assert order.is_toggle_ctrl_value is False

        # WHEN
        order.is_toggle_ctrl_value = True
        order.save()

        # THEN
        updated_order = Order.objects.get(pk=order.pk)
        assert updated_order.is_toggle_ctrl_value is True


# ─── TestOrderDeletion ──────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderDeletion:
    """Tests for deletion of the Order model."""

    def test_delete_order(self, order_data):
        """
        GIVEN: an existing Order
        WHEN: deleting this Order
        THEN: the Order no longer exists in the database
        """
        # GIVEN
        order = Order.objects.create(**order_data)
        order_id = order.pk

        # WHEN
        order.delete()

        # THEN
        assert not Order.objects.filter(pk=order_id).exists()

    def test_delete_multiple_orders(self, sensor, controller):
        """
        GIVEN: multiple existing Orders
        WHEN: deleting all Orders
        THEN: no Orders exist in the database
        """
        # GIVEN
        Order.objects.create(name="Order 1", action_type="get", sensor=sensor)
        Order.objects.create(name="Order 2", action_type="set", controller=controller)
        Order.objects.create(name="Order 3", action_type="get", controller=controller)
        assert Order.objects.count() == 3

        # WHEN
        Order.objects.all().delete()

        # THEN
        assert Order.objects.count() == 0


# ─── TestOrderManager ───────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderManager:
    """Tests for Order model custom manager (enabled)."""

    def test_enabled_manager_returns_only_enabled_orders(self, sensor, controller):
        """
        GIVEN: multiple Orders with different enabled statuses
        WHEN: querying with the enabled manager
        THEN: only enabled Orders are returned
        """
        # GIVEN
        enabled_order1 = Order.objects.create(
            name="Enabled 1",
            action_type="get",
            is_enabled=True,
            sensor=sensor,
        )
        enabled_order2 = Order.objects.create(
            name="Enabled 2",
            action_type="set",
            is_enabled=True,
            controller=controller,
        )
        Order.objects.create(
            name="Disabled",
            action_type="get",
            is_enabled=False,
            sensor=sensor,
        )

        # WHEN
        enabled_orders = Order.enabled.all()

        # THEN
        assert enabled_orders.count() == 2
        assert enabled_order1 in enabled_orders
        assert enabled_order2 in enabled_orders


# ─── TestOrderPrepopulatedSlug ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderPrepopulatedSlug:
    """Tests for Order prepopulated_slug method."""

    def test_prepopulated_slug_returns_name(self, order_data):
        """
        GIVEN: an Order with a name
        WHEN: calling the prepopulated_slug method
        THEN: it returns the Order's name
        """
        # GIVEN
        order = Order.objects.create(**order_data)

        # WHEN
        result = order.prepopulated_slug()

        # THEN
        assert result == order.name

    def test_prepopulated_slug_with_different_names(self, sensor):
        """
        GIVEN: multiple Orders with different names
        WHEN: calling prepopulated_slug on each
        THEN: each returns its respective name
        """
        # GIVEN
        names = ["Order One", "Order Two", "Order Three"]

        for name in names:
            # WHEN
            order = Order.objects.create(name=name, action_type="get", sensor=sensor)
            result = order.prepopulated_slug()

            # THEN
            assert result == name
