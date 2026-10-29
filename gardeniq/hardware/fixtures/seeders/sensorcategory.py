from pathlib import Path

from gardeniq.base.fixtures.seeders import BaseSeeder
from gardeniq.hardware.models import SensorCategory
from gardeniq.hardware.serializers import SensorCategorySeederSerializer


class SensorCategorySeeder(BaseSeeder):
    root_dir_source = Path(__file__).resolve().parents[1]
    filename = "sensor_categories.json"
    model = SensorCategory
    serializer = SensorCategorySeederSerializer
