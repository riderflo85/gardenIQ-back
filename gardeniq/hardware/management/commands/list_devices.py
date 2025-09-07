from django.conf import settings
from django.core.management import BaseCommand

from gardeniq.hardware.utils import list_connected_devices


class Command(BaseCommand):
    help = "List connected devices."

    def add_arguments(self, parser):
        parser.add_argument("--verbose", action="store_true", help="Show more devices infos.")

    def handle(self, *args, **options):
        str_output_format = settings.LD_FORMATS.STR
        devices_infos = list_connected_devices(str_output_format, options["verbose"])
        if isinstance(devices_infos, str):
            self.stdout.write(devices_infos)
