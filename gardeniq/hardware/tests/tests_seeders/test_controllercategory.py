import pytest

from gardeniq.hardware.fixtures.seeders import ControllerCategorySeeder
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.serializers import ControllerCategorySeederSerializer


@pytest.mark.django_db
class TestControllerCategorySeeder:

    @pytest.fixture
    def success_logs(self):
        return []

    @pytest.fixture
    def error_logs(self):
        return []

    @pytest.fixture
    def controller_category_seeder(self, success_logs, error_logs):
        return ControllerCategorySeeder(
            success_logger=lambda msg: success_logs.append(msg),
            error_logger=lambda msg: error_logs.append(msg),
        )

    def test_seeder_attributes(self, controller_category_seeder):
        """The seeder targets ControllerCategory and its source file exists."""
        # WHEN / THEN
        assert controller_category_seeder.model is ControllerCategory
        assert controller_category_seeder.serializer is ControllerCategorySeederSerializer
        assert controller_category_seeder.filename == "controller_categories.json"
        assert controller_category_seeder.source_file.exists()

    def test_seed_creates_relay_when_db_is_empty(self, controller_category_seeder, success_logs):
        """Seeding an empty database creates the Relais pour électrovanne category."""
        # GIVEN
        assert ControllerCategory.objects.count() == 0

        # WHEN
        controller_category_seeder.seed()

        # THEN
        assert ControllerCategory.objects.count() == 1
        assert len(success_logs) == 1
        category = ControllerCategory.objects.get(seed_id=1)
        assert category.name == "Relais pour électrovanne"
        assert category.is_ready is True
        assert category.pin_init_cfg == {"c": "Pin", "a": {"id": "@pin"}}

    def test_seed_skips_when_entries_already_exist(self, controller_category_seeder, error_logs):
        """A second seed without authorize_update does not create duplicates."""
        # GIVEN
        controller_category_seeder.seed()

        # WHEN
        controller_category_seeder.seed()

        # THEN
        assert ControllerCategory.objects.count() == 1
        assert len(error_logs) == 1

    def test_seed_updates_entry_when_authorize_update_is_true(self, controller_category_seeder):
        """seed(authorize_update=True) restores the source data of an existing entry."""
        # GIVEN
        controller_category_seeder.seed()
        ControllerCategory.objects.filter(seed_id=1).update(name="Old name")

        # WHEN
        controller_category_seeder.seed(authorize_update=True)

        # THEN
        assert ControllerCategory.objects.count() == 1
        assert ControllerCategory.objects.get(seed_id=1).name == "Relais pour électrovanne"
