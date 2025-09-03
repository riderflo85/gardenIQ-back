from pathlib import Path

from gardeniq.base.fixtures.seeders import BaseSeeder


class OrderlgSeeder(BaseSeeder):
    root_dir_source = Path(__file__).resolve().parents[1]
