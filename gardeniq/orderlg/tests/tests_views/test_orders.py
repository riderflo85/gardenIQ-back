from django.db.models import Model

from rest_framework import status

import pytest

from gardeniq.base.utils.tests import ViewSetTestMixin
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
        order1 = Order.objects.create(name="Test Order 1", description="First test order", action_type="get")
        order2 = Order.objects.create(name="Test Order 2", description="Second test order", action_type="set")
        return order1, order2


@pytest.mark.django_db
class TestOrderAPIModelView(OrderViewSetTestConf):
    def test_list(self, authenticated_client, obj):
        """Test retrieving the list of orders."""
        # GIVEN
        order1, order2 = obj  # Orders created via fixture
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.get(url)

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
        assert "action_type" in first_order
        assert "is_enabled" in first_order

    def test_retrieve(self, authenticated_client, obj):
        """Test retrieving a specific order."""
        # GIVEN
        order1, _ = obj  # Order created via fixture
        url = self.get_url_detail(order1.pk)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == order1.name
        assert response.data["description"] == order1.description
        assert response.data["action_type"] == order1.action_type

    def test_create(self, authenticated_client):
        """Test creating a new order."""
        # GIVEN
        valid_payload = {
            "name": "New Order",
            "description": "A new test order",
            "action_type": "get",
        }
        url = self.get_url_create()

        # WHEN
        response = authenticated_client.post(url, valid_payload, format="json")

        # THEN
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == valid_payload["name"]
        assert response.data["description"] == valid_payload["description"]
        assert response.data["action_type"] == valid_payload["action_type"]

        # Check if the order was actually created in the database
        assert Order.objects.filter(name=valid_payload["name"]).exists()

    def test_update(self, authenticated_client, obj):
        """Test updating an existing order."""
        # GIVEN
        order1, _ = obj  # Order to update
        url = self.get_url_detail(order1.pk)
        update_data = {
            "name": "Updated Order",
            "description": "Updated description",
            "action_type": "set",
        }

        # WHEN
        response = authenticated_client.put(url, update_data, format="json")

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == update_data["name"]
        assert response.data["description"] == update_data["description"]
        assert response.data["action_type"] == update_data["action_type"]

        # Check if the order was actually updated in the database
        updated_order = Order.objects.get(pk=order1.pk)
        assert updated_order.name == update_data["name"]
        assert updated_order.action_type == update_data["action_type"]

    def test_delete(self, authenticated_client, obj):
        """Test deleting an order."""
        # GIVEN
        order1, _ = obj  # Order to delete
        url = self.get_url_detail(order1.pk)

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Check if the order was actually deleted from the database
        with pytest.raises(Order.DoesNotExist):
            Order.objects.get(pk=order1.pk)
