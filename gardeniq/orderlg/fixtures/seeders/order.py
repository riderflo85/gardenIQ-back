from .orderlg import OrderlgSeeder
from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import OrderSerializer


class OrderSeeder(OrderlgSeeder):
    filename = "orders.json"
    model = Order
    serializer = OrderSerializer
    search_field_name = "slug"
    dependencies = [
        "ArgumentSeeder",
    ]
