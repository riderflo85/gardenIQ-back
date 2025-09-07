from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import OrderSerializer

from .orderlg import OrderlgSeeder


class OrderSeeder(OrderlgSeeder):
    filename = "orders.json"
    model = Order
    serializer = OrderSerializer
    search_field_name = "slug"
    dependencies = [
        "ArgumentSeeder",
    ]
