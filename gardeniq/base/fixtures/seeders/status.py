from pathlib import Path

from gardeniq.base.fixtures.seeders import BaseSeeder
from gardeniq.base.models import Status
from gardeniq.base.serializers import StatusSerializer


class StatusSeeder(BaseSeeder):
    root_dir_source = Path(__file__).resolve().parents[1]
    filename = "status.json"
    model = Status
    serializer = StatusSerializer
    search_field_name = ["name", "tag"]
