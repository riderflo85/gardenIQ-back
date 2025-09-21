import pytest

from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import OrderDetailReadOnlySerializer
from gardeniq.orderlg.serializers import OrderSerializer


@pytest.fixture
def create_arguments():
    arg1 = Argument.objects.create(
        description="Test Argument 1",
        slug="test-argument-1",
        value_type="int",
    )
    arg2 = Argument.objects.create(
        description="Test Argument 2",
        slug="test-argument-2",
        value_type="int",
    )
    return arg1, arg2


@pytest.fixture
def create_order(create_arguments):
    arg1, arg2 = create_arguments
    order = Order.objects.create(
        name="Test Order",
        description="Test Order Description",
        action_type="get",
    )
    order.arguments.set([arg1, arg2])
    return order


@pytest.mark.django_db
class TestOrderSerializer:
    def test_valide_serializer(self, create_arguments):
        arg1, arg2 = create_arguments
        # GIVEN
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "get",
            "arguments": [arg1.pk, arg2.pk],
        }
        expected = {
            "name": "Test Order",
            "description": "Test Order Description",
            "slug": "test-order",
            "action_type": "get",
            "arguments": [arg1.pk, arg2.pk],
            "is_enabled": True,
        }

        # WHEN
        serializer = OrderSerializer(data=data)

        # THEN
        serializer.is_valid()
        assert serializer.is_valid()
        assert serializer.data == expected

    def test_create_order(self, create_arguments):
        arg1, arg2 = create_arguments
        # GIVEN
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "get",
            "arguments": [arg1.pk, arg2.pk],
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
        assert order.arguments.count() == 2

    def test_create_order_with_custom_slug(self, create_arguments):
        arg1, arg2 = create_arguments
        # GIVEN
        data = {
            "name": "Test Order",
            "slug": "my-custom-slug-test-order",
            "description": "Test Order Description",
            "action_type": "get",
            "arguments": [arg1.pk, arg2.pk],
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
        assert order.arguments.count() == 2

    def test_update_serializer(self, create_arguments):
        arg1, arg2 = create_arguments
        # GIVEN
        data = {
            "name": "Test Update Order",
            "description": "Test Update Order Description",
            "action_type": "set",
        }
        order = Order.objects.create(**data)
        order.arguments.set([arg1])
        updated_data = {
            "name": "New name for Test Update Order",
            "description": "New description for Test Update Order Description",
            "action_type": "get",
            "arguments": [arg1.pk, arg2.pk],
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
        assert order.arguments.count() == 2


@pytest.mark.django_db
class TestOrderDetailReadOnlySerializer:
    def test_cannot_create_order_serializer(self):
        # GIVEN
        order_count_before = Order.objects.count()
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "get",
            "arguments": [
                {
                    "description": "my description, blabla",
                    "slug": "my-description-blabla",
                    "is_enabled": True,
                    "value_type": "int",
                    "required": True,
                    "is_option": False,
                },
            ],
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

    def test_detail_serializer(self, create_order):
        # GIVEN
        order = create_order
        expected = {
            "id": order.pk,
            "name": order.name,
            "description": order.description,
            "slug": order.slug,
            "action_type": order.action_type,
            "is_enabled": order.is_enabled,
            "arguments": [
                {
                    "id": arg.pk,
                    "description": arg.description,
                    "slug": arg.slug,
                    "is_enabled": arg.is_enabled,
                    "value_type": arg.value_type,
                    "required": arg.required,
                    "is_option": arg.is_option,
                }
                for arg in order.arguments.all()
            ],
        }

        # WHEN
        serializer = OrderDetailReadOnlySerializer(instance=order)

        # THEN
        assert serializer.data == expected
