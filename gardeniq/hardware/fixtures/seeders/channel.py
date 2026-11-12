from pathlib import Path

from gardeniq.base.fixtures.seeders import BaseSeeder
from gardeniq.hardware.models import Channel
from gardeniq.hardware.serializers import ChannelSeederSerializer


class ChannelSeeder(BaseSeeder):
    root_dir_source = Path(__file__).resolve().parents[1]
    filename = "channels.json"
    model = Channel
    serializer = ChannelSeederSerializer
