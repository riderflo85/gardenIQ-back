import serial

from django.core.management import BaseCommand
from django.conf import settings

from gardeniq.hardware.utils import list_connected_devices


class Command(BaseCommand):
    help = "Exchange a text with the card hardware USB connected."

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
        ser = serial.Serial(timeout=0.2)
        ser.baudrate = options['baud']
        ser.port = options['port']
        ser.open()
        if ser.is_open:
            self.stdout.write(self.style.SUCCESS('Connection opened !\nTape q to quit prompt.'))
            ser.flush()
            while True:
                hardware_msg = ser.read_until().strip()
                self.stdout.write('HDW : %s' % hardware_msg.decode())
                text = input('>>> ')
                if text == 'q':
                    break
                ser.write(f'{text}\r'.encode())
        else:
            self.stdout.write(self.style.ERROR('Test hardware connection is failed !'))
        ser.close()
