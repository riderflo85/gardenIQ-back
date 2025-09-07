from enum import Enum


class ListDevicesFormat(Enum):
    STR = "str"
    LIST_DEVICES = "list_devices"
    LIST_NAMES = "list_names"


# Baudrate card transmission
BAUDRATE = 9600

# Register ListDevicesFormat class in a contante to call this class with django.conf.settings
LD_FORMATS = ListDevicesFormat
