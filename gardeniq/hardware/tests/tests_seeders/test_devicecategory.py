import pytest

from gardeniq.hardware.fixtures.seeders import DeviceCategorySeeder
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.serializers import DeviceCategorySeederSerializer


@pytest.mark.django_db
class TestDeviceCategorySeeder:

    @pytest.fixture
    def success_logs(self):
        return []

    @pytest.fixture
    def error_logs(self):
        return []

    @pytest.fixture
    def device_category_seeder(self, success_logs, error_logs):
        return DeviceCategorySeeder(
            success_logger=lambda msg: success_logs.append(msg),
            error_logger=lambda msg: error_logs.append(msg),
        )

    def test_seeder_attributes(self, device_category_seeder):
        """The seeder targets DeviceCategory and its source file exists."""
        # WHEN / THEN
        assert device_category_seeder.model is DeviceCategory
        assert device_category_seeder.serializer is DeviceCategorySeederSerializer
        assert device_category_seeder.filename == "device_categories.json"
        assert device_category_seeder.source_file.exists()

    def test_seed_creates_pico_when_db_is_empty(self, device_category_seeder, success_logs):
        """Seeding an empty database creates the Raspberry Pi Pico category."""
        # GIVEN
        assert DeviceCategory.objects.count() == 0

        # WHEN
        device_category_seeder.seed()

        # THEN
        assert DeviceCategory.objects.count() == 1
        assert len(success_logs) == 1
        category = DeviceCategory.objects.get(seed_id=1)
        assert category.name == "Raspberry PiPico"
        assert category.is_ready is True
        assert len(category.pins_configuration["digits"]) == 29
        assert category.pins_configuration["available_channels"] == ["digit", "analog"]

    def test_seed_skips_when_entries_already_exist(self, device_category_seeder, error_logs):
        """A second seed without authorize_update does not create duplicates."""
        # GIVEN
        device_category_seeder.seed()

        # WHEN
        device_category_seeder.seed()

        # THEN
        assert DeviceCategory.objects.count() == 1
        assert len(error_logs) == 1

    def test_seed_updates_entry_when_authorize_update_is_true(self, device_category_seeder):
        """seed(authorize_update=True) restores the source data of an existing entry."""
        # GIVEN
        device_category_seeder.seed()
        DeviceCategory.objects.filter(seed_id=1).update(name="Old name")

        # WHEN
        device_category_seeder.seed(authorize_update=True)

        # THEN
        assert DeviceCategory.objects.count() == 1
        assert DeviceCategory.objects.get(seed_id=1).name == "Raspberry PiPico"
