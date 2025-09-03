from .orderlg import OrderlgSeeder
from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.serializers import ArgumentSerializer


class ArgumentSeeder(OrderlgSeeder):
    filename = "arguments.json"
    model = Argument
    serializer = ArgumentSerializer
    search_field_name = "slug"
