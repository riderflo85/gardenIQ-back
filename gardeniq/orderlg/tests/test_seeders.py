import pytest

from gardeniq.orderlg.fixtures.seeders import OrderSeeder
from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import OrderSeederSerializer


@pytest.mark.django_db
class TestOrderSeeder:

    @pytest.fixture
    def success_logs(self):
        return []

    @pytest.fixture
    def error_logs(self):
        return []

    @pytest.fixture
    def order_seeder(self, success_logs, error_logs):
        return OrderSeeder(
            success_logger=lambda msg: success_logs.append(msg),
            error_logger=lambda msg: error_logs.append(msg),
        )

    # ── Attributs du seeder ───────────────────────────────────────────────────

    def test_seeder_model_is_order(self, order_seeder):
        assert order_seeder.model is Order

    def test_seeder_serializer_is_order_seeder_serializer(self, order_seeder):
        assert order_seeder.serializer is OrderSeederSerializer

    def test_seeder_filename(self, order_seeder):
        assert order_seeder.filename == "orders.json"

    def test_seeder_search_field_name(self, order_seeder):
        assert order_seeder.search_field_name == ["seed_id", "slug"]

    def test_seeder_source_file_exists(self, order_seeder):
        assert order_seeder.source_file.exists()

    # ── seed() — base de données vide ────────────────────────────────────────

    def test_seed_creates_all_entries_when_db_is_empty(self, order_seeder, success_logs):
        # GIVEN
        assert Order.objects.count() == 0

        # WHEN
        order_seeder.seed()

        # THEN
        assert Order.objects.count() == 2
        assert len(success_logs) == 2

    def test_seed_creates_turn_on_led_order(self, order_seeder):
        # WHEN
        order_seeder.seed()

        # THEN
        order = Order.objects.get(slug="turn_on_led")
        assert order.seed_id == 1
        assert order.name == "Allumer la LED onboard"
        assert order.description == "Allumer la LED intégrée à la carte."
        assert order.action_type == "set"
        assert order.is_ready is False
        assert order.is_toggle_ctrl_value is True
        assert order.sensor is None
        assert order.controller is None

    def test_seed_creates_get_temp_order(self, order_seeder):
        # WHEN
        order_seeder.seed()

        # THEN
        order = Order.objects.get(slug="get_temp")
        assert order.seed_id == 2
        assert order.name == "Récupérer la température"
        assert order.description == "Récupérer la température de la sonde."
        assert order.action_type == "get"
        assert order.is_ready is False
        assert order.sensor is None
        assert order.controller is None

    # ── seed() — base de données non vide sans authorize_update ──────────────

    def test_seed_skips_creation_when_entries_already_exist(self, order_seeder, error_logs):
        # GIVEN
        Order.objects.create(seed_id=99, name="Existing Order", slug="existing", action_type="set", is_ready=False)

        # WHEN
        order_seeder.seed()

        # THEN
        assert Order.objects.count() == 1
        assert len(error_logs) == 1

    def test_seed_does_not_create_duplicates_on_second_call(self, order_seeder, error_logs):
        # GIVEN
        order_seeder.seed()

        # WHEN — deuxième appel sans authorize_update
        order_seeder.seed()

        # THEN
        assert Order.objects.count() == 2
        assert len(error_logs) == 1

    # ── seed(authorize_update=True) ───────────────────────────────────────────

    def test_seed_updates_entries_when_authorize_update_is_true(self, order_seeder, success_logs):
        # GIVEN — les deux entrées existent déjà avec les bons seed_id/slug
        Order.objects.create(
            seed_id=1,
            slug="turn_on_led",
            name="Old Name 1",
            description="Old desc 1",
            action_type="set",
            is_ready=False,
        )
        Order.objects.create(
            seed_id=2, slug="get_temp", name="Old Name 2", description="Old desc 2", action_type="get", is_ready=False
        )

        # WHEN
        order_seeder.seed(authorize_update=True)

        # THEN
        assert Order.objects.count() == 2
        updated = Order.objects.get(slug="turn_on_led")
        assert updated.name == "Allumer la LED onboard"
        assert updated.description == "Allumer la LED intégrée à la carte."
        assert len(success_logs) == 2

    def test_seed_creates_missing_entry_during_update(self, order_seeder, success_logs):
        # GIVEN — seul seed_id=1 existe ; seed_id=2 doit être créé lors de la mise à jour
        Order.objects.create(
            seed_id=1,
            slug="turn_on_led",
            name="Allumer la LED onboard",
            description="Allumer la LED intégrée à la carte.",
            action_type="set",
            is_ready=False,
        )

        # WHEN
        order_seeder.seed(authorize_update=True)

        # THEN
        assert Order.objects.count() == 2
        assert Order.objects.filter(seed_id=2, slug="get_temp").exists()

    # ── _create_entries() ─────────────────────────────────────────────────────

    def test_create_entries_creates_a_single_entry(self, order_seeder, success_logs):
        # GIVEN
        data = [
            {
                "seed_id": 10,
                "is_ready": False,
                "name": "Test Order",
                "slug": "test_order",
                "description": "A test order.",
                "action_type": "set",
                "sensor": None,
                "controller": None,
            }
        ]

        # WHEN
        order_seeder._create_entries(data)

        # THEN
        assert Order.objects.count() == 1
        assert len(success_logs) == 1
        order = Order.objects.get(slug="test_order")
        assert order.seed_id == 10
        assert order.is_ready is False
