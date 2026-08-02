from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import OrderSeederSerializer

from .orderlg import OrderlgSeeder


class OrderSeeder(OrderlgSeeder):
    filename = "orders.json"
    model = Order
    serializer = OrderSeederSerializer
    search_field_name = OrderlgSeeder.search_field_name + ["slug"]
