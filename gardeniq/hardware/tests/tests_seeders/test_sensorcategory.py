import pytest

from gardeniq.hardware.fixtures.seeders import SensorCategorySeeder
from gardeniq.hardware.models import SensorCategory
from gardeniq.hardware.serializers import SensorCategorySeederSerializer


@pytest.mark.django_db
class TestSensorCategorySeeder:

    @pytest.fixture
    def success_logs(self):
        return []

    @pytest.fixture
    def error_logs(self):
        return []

    @pytest.fixture
    def sensor_category_seeder(self, success_logs, error_logs):
        return SensorCategorySeeder(
            success_logger=lambda msg: success_logs.append(msg),
            error_logger=lambda msg: error_logs.append(msg),
        )

    def test_seeder_attributes(self, sensor_category_seeder):
        """The seeder targets SensorCategory and its source file exists."""
        # WHEN / THEN
        assert sensor_category_seeder.model is SensorCategory
        assert sensor_category_seeder.serializer is SensorCategorySeederSerializer
        assert sensor_category_seeder.filename == "sensor_categories.json"
        assert sensor_category_seeder.source_file.exists()

    def test_seed_creates_temperature_when_db_is_empty(self, sensor_category_seeder, success_logs):
        """Seeding an empty database creates the Temperature °C category."""
        # GIVEN
        assert SensorCategory.objects.count() == 0

        # WHEN
        sensor_category_seeder.seed()

        # THEN
        assert SensorCategory.objects.count() == 1
        assert len(success_logs) == 1
        category = SensorCategory.objects.get(seed_id=1)
        assert category.name == "Temperature °C"
        assert category.is_ready is True
        assert category.pin_init_cfg == {"c": "ADC", "a": {"id": "@pin"}}
        assert category.unity_value == "°C"

    def test_seed_skips_when_entries_already_exist(self, sensor_category_seeder, error_logs):
        """A second seed without authorize_update does not create duplicates."""
        # GIVEN
        sensor_category_seeder.seed()

        # WHEN
        sensor_category_seeder.seed()

        # THEN
        assert SensorCategory.objects.count() == 1
        assert len(error_logs) == 1

    def test_seed_updates_entry_when_authorize_update_is_true(self, sensor_category_seeder):
        """seed(authorize_update=True) restores the source data of an existing entry."""
        # GIVEN
        sensor_category_seeder.seed()
        SensorCategory.objects.filter(seed_id=1).update(name="Old name")

        # WHEN
        sensor_category_seeder.seed(authorize_update=True)

        # THEN
        assert SensorCategory.objects.count() == 1
        assert SensorCategory.objects.get(seed_id=1).name == "Temperature °C"
