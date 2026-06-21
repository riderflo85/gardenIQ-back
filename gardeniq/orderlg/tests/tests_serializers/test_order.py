import pytest

from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import OrderDetailReadOnlySerializer
from gardeniq.orderlg.serializers import OrderListReadOnlySerializer
from gardeniq.orderlg.serializers import OrderSerializer


@pytest.fixture
def create_order():
    order = Order.objects.create(
        name="Test Order",
        description="Test Order Description",
        action_type="get",
    )
    return order


@pytest.mark.django_db
class TestOrderSerializer:
    def test_valide_serializer(self):
        # GIVEN
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "get",
        }
        expected = {
            "name": "Test Order",
            "description": "Test Order Description",
            "slug": "test-order",
            "action_type": "get",
            "is_enabled": True,
        }

        # WHEN
        serializer = OrderSerializer(data=data)

        # THEN
        serializer.is_valid()
        assert serializer.is_valid()
        assert serializer.data == expected

    def test_create_order(self):
        # GIVEN
        data = {
            "name": "Test Order",
            "description": "Test Order Description",
            "action_type": "get",
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

    def test_create_order_with_custom_slug(self):
        # GIVEN
        data = {
            "name": "Test Order",
            "slug": "my-custom-slug-test-order",
            "description": "Test Order Description",
            "action_type": "get",
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

    def test_update_serializer(self):
        # GIVEN
        data = {
            "name": "Test Update Order",
            "description": "Test Update Order Description",
            "action_type": "set",
        }
        order = Order.objects.create(**data)
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

    def test_list_serializer(self, create_order):
        # GIVEN
        order = create_order
        expected = {
            "id": order.pk,
            "name": order.name,
            "slug": order.slug,
            "action_type": order.action_type,
            "is_enabled": order.is_enabled,
        }

        # WHEN
        serializer = OrderListReadOnlySerializer(instance=order)

        # THEN
        assert serializer.data == expected

    def test_list_serializer_multiple_orders(self):
        # GIVEN
        order1 = Order.objects.create(
            name="First Order",
            description="First Description",
            action_type="get",
        )

        order2 = Order.objects.create(
            name="Second Order",
            description="Second Description",
            action_type="set",
        )

        expected = [
            {
                "id": order1.pk,
                "name": order1.name,
                "slug": order1.slug,
                "action_type": order1.action_type,
                "is_enabled": order1.is_enabled,
            },
            {
                "id": order2.pk,
                "name": order2.name,
                "slug": order2.slug,
                "action_type": order2.action_type,
                "is_enabled": order2.is_enabled,
            },
        ]

        # WHEN
        serializer = OrderListReadOnlySerializer(instance=[order1, order2], many=True)

        # THEN
        assert serializer.data == expected


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
        }

        # WHEN
        serializer = OrderDetailReadOnlySerializer(instance=order)

        # THEN
        assert serializer.data == expected
