import pytest

from gardeniq.orderlg.fixtures.seeders import ArgumentSeeder
from gardeniq.orderlg.fixtures.seeders import OrderSeeder
from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.models import Order


@pytest.mark.django_db
class TestUseSeeders:
    def test_argument_seeder(self):
        # GIVEN
        arg_seeder = ArgumentSeeder(print, print)
        argument_model = arg_seeder.model
        argument_count_before_seed = argument_model.objects.count()

        # WHEN
        arg_seeder.seed()
        argument_count_after_seed = argument_model.objects.count()
        new_argument = argument_model.objects.get(slug="-s")

        # THEN
        assert argument_count_before_seed < argument_count_after_seed
        assert isinstance(new_argument, Argument)
        assert new_argument.description == "Sonde demandée.\nNuméro du PIN sur la carte.\nOUNuméro de l’objet sonde."
        assert new_argument.value_type == "int"

    def test_order_seeder(self):
        # GIVEN
        # seed arguments before orders
        arg_seeder = ArgumentSeeder(print, print)
        arg_seeder.seed()
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
        assert new_order.arguments.count() == 1
