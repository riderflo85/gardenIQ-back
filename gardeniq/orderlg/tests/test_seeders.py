import pytest

from gardeniq.orderlg.fixtures.seeders import OrderSeeder
from gardeniq.orderlg.models import Order


@pytest.mark.django_db
class TestUseSeeders:

    def test_order_seeder(self):
        # GIVEN
        # seed arguments before orders
        order_seeder = OrderSeeder(print, print)
        order_model = order_seeder.model
        order_count_before_seed = order_model.objects.count()

        # WHEN
        order_seeder.seed()
        order_count_after_seed = order_model.objects.count()
        new_order = order_model.objects.get(slug="get_temp")

        # THEN
        assert order_count_before_seed < order_count_after_seed
        assert isinstance(new_order, Order)
        assert new_order.name == "Récupérer la température"
        assert new_order.description == "Récupérer la température de la sonde passée en argument."
        assert new_order.action_type == "get"
