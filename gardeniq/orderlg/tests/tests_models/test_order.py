import pytest

from gardeniq.orderlg.models import Order


@pytest.fixture
def order_data():
    """Fixture providing basic data to create an Order."""
    return {
        "name": "Get Temperature",
        "description": "Retrieve temperature from sensor",
        "slug": "get-temperature",
        "action_type": "get",
    }


@pytest.fixture
def order_setter_data():
    """Fixture providing data for a setter Order."""
    return {
        "name": "Set LED State",
        "description": "Set the state of the LED",
        "slug": "set-led-state",
        "action_type": "set",
    }


@pytest.fixture
def order_minimal_data():
    """Fixture providing minimal data relying on defaults."""
    return {
        "name": "Check Status",
        "action_type": "get",
    }


@pytest.mark.django_db
class TestOrderCreation:
    """Tests for Order model creation."""

    def test_create_order_with_all_fields(self, order_data):
        """
        GIVEN: complete data for an Order
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
        assert order.is_enabled is True  # from ProtectedDisabledMixinModel

    def test_create_order_with_minimal_data(self, order_minimal_data):
        """
        GIVEN: minimal data for an Order
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


@pytest.mark.django_db
class TestOrderFields:
    """Tests for Order model fields and constraints."""

    def test_name_field(self, order_data):
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
        )

        # THEN
        assert order.name == name

    def test_description_field(self, order_data):
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
        )

        # THEN
        assert order.description == long_description

    def test_slug_field(self, order_data):
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
        )

        # THEN
        assert order.slug == slug

    def test_action_type_field_getter(self):
        """
        GIVEN: action_type='get'
        WHEN: creating an Order with getter action
        THEN: the action_type field is set to 'get'
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Getter Order",
            action_type="get",
        )

        # THEN
        assert order.action_type == "get"

    def test_action_type_field_setter(self):
        """
        GIVEN: action_type='set'
        WHEN: creating an Order with setter action
        THEN: the action_type field is set to 'set'
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Setter Order",
            action_type="set",
        )

        # THEN
        assert order.action_type == "set"

    def test_is_enabled_field_default_is_true(self):
        """
        GIVEN: data without specifying is_enabled field
        WHEN: creating an Order
        THEN: the is_enabled field defaults to True
        """
        # GIVEN / WHEN
        order = Order.objects.create(
            name="Test Order",
            action_type="get",
        )

        # THEN
        assert order.is_enabled is True


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

    def test_update_order_action_type(self, order_data):
        """
        GIVEN: an existing Order with action_type='get'
        WHEN: updating its action_type to 'set'
        THEN: the action_type is modified correctly
        """
        # GIVEN
        order = Order.objects.create(**order_data)
        assert order.action_type == "get"

        # WHEN
        order.action_type = "set"
        order.save()

        # THEN
        updated_order = Order.objects.get(pk=order.pk)
        assert updated_order.action_type == "set"

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

    def test_delete_multiple_orders(self):
        """
        GIVEN: multiple existing Orders
        WHEN: deleting all Orders
        THEN: no Orders exist in the database
        """
        # GIVEN
        Order.objects.create(name="Order 1", action_type="get")
        Order.objects.create(name="Order 2", action_type="set")
        Order.objects.create(name="Order 3", action_type="get")
        assert Order.objects.count() == 3

        # WHEN
        Order.objects.all().delete()

        # THEN
        assert Order.objects.count() == 0


@pytest.mark.django_db
class TestOrderManager:
    """Tests for Order model custom manager (enabled)."""

    def test_enabled_manager_returns_only_enabled_orders(self):
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
        )
        enabled_order2 = Order.objects.create(
            name="Enabled 2",
            action_type="set",
            is_enabled=True,
        )
        Order.objects.create(
            name="Disabled",
            action_type="get",
            is_enabled=False,
        )

        # WHEN
        enabled_orders = Order.enabled.all()

        # THEN
        assert enabled_orders.count() == 2
        assert enabled_order1 in enabled_orders
        assert enabled_order2 in enabled_orders


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

    def test_prepopulated_slug_with_different_names(self):
        """
        GIVEN: multiple Orders with different names
        WHEN: calling prepopulated_slug on each
        THEN: each returns its respective name
        """
        # GIVEN
        names = ["Order One", "Order Two", "Order Three"]

        for name in names:
            # WHEN
            order = Order.objects.create(name=name, action_type="get")
            result = order.prepopulated_slug()

            # THEN
            assert result == name
