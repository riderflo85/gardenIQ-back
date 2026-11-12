from pathlib import Path

from gardeniq.base.fixtures.seeders import BaseSeeder
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.serializers import DeviceCategorySeederSerializer


class DeviceCategorySeeder(BaseSeeder):
    root_dir_source = Path(__file__).resolve().parents[1]
    filename = "device_categories.json"
    model = DeviceCategory
    serializer = DeviceCategorySeederSerializer
