from django.db.models import Model

from rest_framework import status

import pytest

from gardeniq.base.utils.tests import ViewSetTestMixin
from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.models import Order


@pytest.mark.django_db
class OrderViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "orders"
    MODEL = Order
    DATA_TO_DEFAULT_OBJ = {
        "name": "Default Order",
        "description": "Default test order",
        "action_type": "get",
    }

    def generate_default_obj(self) -> tuple[Model, Model]:
        arg1 = Argument.objects.create(
            description="Test argument 1",
            slug="test-arg1",
            value_type="str",
            required=True,
            is_option=False,
        )
        arg2 = Argument.objects.create(
            description="Test argument 2",
            slug="test-arg2",
            value_type="int",
            required=False,
            is_option=False,
        )

        # Create many orders for tests
        order1 = Order.objects.create(name="Test Order 1", description="First test order", action_type="get")
        order1.arguments.set([arg1])

        order2 = Order.objects.create(name="Test Order 2", description="Second test order", action_type="set")
        order2.arguments.set([arg1, arg2])
        return order1, order2


@pytest.mark.django_db
class TestOrderAPIModelView(OrderViewSetTestConf):
    def test_list(self, client_anonymous, obj):
        """Test retrieving the list of orders."""
        # GIVEN
        order1, order2 = obj  # Orders created via fixture
        url = self.get_url_list()

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

        # Check if expected orders are present in the response
        order_names = [order["name"] for order in response.data["results"]]
        assert order1.name in order_names
        assert order2.name in order_names

        # Check response data format
        first_order = response.data["results"][0]
        assert "name" in first_order
        assert "description" in first_order
        assert "action_type" in first_order
        assert "is_enabled" in first_order
        assert "arguments" in first_order

    def test_retrieve(self, client_anonymous, obj):
        """Test retrieving a specific order."""
        # GIVEN
        order1, _ = obj  # Order created via fixture
        url = self.get_url_detail(order1.pk)

        # WHEN
        response = client_anonymous.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == order1.name
        assert response.data["description"] == order1.description
        assert response.data["action_type"] == order1.action_type
        assert len(response.data["arguments"]) == 1
        assert response.data["arguments"][0]["id"] == order1.arguments.first().pk

    def test_create(self, client_anonymous):
        """Test creating a new order."""
        # GIVEN
        new_arg = Argument.objects.create(
            description="Test argument 34",
            slug="test-arg34",
            value_type="str",
            required=True,
            is_option=False,
        )
        valid_payload = {
            "name": "New Order",
            "description": "A new test order",
            "action_type": "get",
            "arguments": [new_arg.pk],
        }
        url = self.get_url_create()

        # WHEN
        response = client_anonymous.post(url, valid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == valid_payload["name"]
        assert response.data["description"] == valid_payload["description"]
        assert response.data["action_type"] == valid_payload["action_type"]
        assert response.data["arguments"] == valid_payload["arguments"]

        # Check if the order was actually created in the database
        assert Order.objects.filter(name=valid_payload["name"]).exists()

    def test_update(self, client_anonymous, obj):
        """Test updating an existing order."""
        # GIVEN
        order1, _ = obj  # Order to update
        url = self.get_url_detail(order1.pk)
        new_arg = Argument.objects.create(
            description="Test argument 54",
            slug="test-arg54",
            value_type="str",
            required=True,
            is_option=False,
        )
        update_data = {
            "name": "Updated Order",
            "description": "Updated description",
            "action_type": "set",
            "arguments": [new_arg.pk],
        }

        # WHEN
        response = client_anonymous.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == update_data["name"]
        assert response.data["description"] == update_data["description"]
        assert response.data["action_type"] == update_data["action_type"]
        assert response.data["arguments"] == update_data["arguments"]

        # Check if the order was actually updated in the database
        updated_order = Order.objects.get(pk=order1.pk)
        assert updated_order.name == update_data["name"]
        assert updated_order.action_type == update_data["action_type"]
        assert list(updated_order.arguments.values_list("pk", flat=True)) == update_data["arguments"]

    def test_delete(self, client_anonymous, obj):
        """Test deleting an order."""
        # GIVEN
        order1, _ = obj  # Order to delete
        url = self.get_url_detail(order1.pk)

        # WHEN
        response = client_anonymous.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Check if the order was actually deleted from the database
        with pytest.raises(Order.DoesNotExist):
            Order.objects.get(pk=order1.pk)
