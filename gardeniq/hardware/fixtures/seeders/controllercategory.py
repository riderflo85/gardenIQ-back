from pathlib import Path

from gardeniq.base.fixtures.seeders import BaseSeeder
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.serializers import ControllerCategorySeederSerializer


class ControllerCategorySeeder(BaseSeeder):
    root_dir_source = Path(__file__).resolve().parents[1]
    filename = "controller_categories.json"
    model = ControllerCategory
    serializer = ControllerCategorySeederSerializer
