from pathlib import Path

from gardeniq.base.fixtures.seeders import BaseSeeder
from gardeniq.base.models import Status
from gardeniq.base.serializers import StatusSeederSerializer


class StatusSeeder(BaseSeeder):
    root_dir_source = Path(__file__).resolve().parents[1]
    filename = "status.json"
    model = Status
    serializer = StatusSeederSerializer
    search_field_name = BaseSeeder.search_field_name + ["name", "tag"]
