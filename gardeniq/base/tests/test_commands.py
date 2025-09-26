from io import StringIO

from django.core.management import call_command

import pytest

from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.models import Order


@pytest.mark.django_db
class TestCommands:
    def test_seed_all_apps_command(self):
        # GIVEN
        arg_counter_before_seed = Argument.objects.count()
        order_counter_before_seed = Order.objects.count()
        out = StringIO()

        # WHEN
        call_command("seed", stdout=out)

        # THEN
        assert Argument.objects.count() > arg_counter_before_seed
        assert Order.objects.count() > order_counter_before_seed

    @pytest.mark.parametrize(
        "app_name, model_obj",
        [
            ("orderlg", [Argument, Order]),
        ],
    )
    def test_seed_with_app_name(self, app_name, model_obj):
        # GIVEN
        object_counters_before_seed = [m.objects.count() for m in model_obj]
        out = StringIO()

        # WHEN
        call_command("seed", app=app_name, stdout=out)
        object_counters_after_seed = [m.objects.count() for m in model_obj]

        # THEN
        assert object_counters_after_seed > object_counters_before_seed
