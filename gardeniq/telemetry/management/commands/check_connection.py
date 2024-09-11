import serial

from django.core.management import BaseCommand
from django.conf import settings

from gardeniq.telemetry.utils import list_connected_devices


class Command(BaseCommand):
    help = "Check if the card hardware is connect."

    def add_arguments(self, parser):
        parser.add_argument(
            'port',
            type=str,
            help='Device port. You can list all devices with list_devices command.'
        )
        parser.add_argument(
            'baud',
            type=int,
            help='Baudrate transmission with device.'
        )

    def handle(self, *args, **options):
        port = options['port']
        if port not in list_connected_devices(settings.LD_FORMATS.LIST_DEVICES):
            self.stderr.write(f'port `{port}` is not found !')
            return False
        ser = serial.Serial()
        ser.baudrate = options['baud']
        ser.port = options['port']
        ser.open()
        if ser.is_open:
            self.stdout.write(self.style.SUCCESS('Test hardware connection is done !'))
            self.stdout.write(self.style.SUCCESS(' Connection closed !'))
        else:
            self.stdout.write(self.style.ERROR('Test hardware connection is failed !'))
        ser.close()
