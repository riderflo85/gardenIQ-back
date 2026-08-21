import re
from enum import Enum

__all__ = [
    "BAUDRATE",
    "LD_FORMATS",
    "PATTERN_SERIAL_PORT",
    "DATASHEET_JSON_SCHEMA",
]


class ListDevicesFormat(Enum):
    STR = "str"
    LIST_DEVICES = "list_devices"
    LIST_NAMES = "list_names"


# Baudrate card transmission
BAUDRATE = 9600

# Register ListDevicesFormat class in a contante to call this class with django.conf.settings
LD_FORMATS = ListDevicesFormat

PATTERN_SERIAL_PORT = re.compile(r"^(\/dev\/(tty(S|USB|ACM)[0-9]+|cu\.[\w\-\.]+)|COM[0-9]+)$")

DATASHEET_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "available_channels": {
            "type": "array",
            "items": {"type": "string"},
        },
        "digits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "pins": {
                        "type": "array",
                        "prefixItems": [{"type": "integer"}],
                    },
                },
                "required": ["name", "pins"],
            },
        },
        "pwms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "pins": {
                        "type": "array",
                        "prefixItems": [{"type": "integer"}],
                    },
                },
                "required": ["name", "pins"],
            },
        },
        "analogs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "pins": {
                        "type": "array",
                        "prefixItems": [{"type": "integer"}],
                    },
                },
                "required": ["name", "pins"],
            },
        },
        "i2cs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "pins": {
                        "type": "array",
                        "prefixItems": [
                            {"type": "integer"},
                            {"type": "integer"},
                        ],
                    },
                },
                "required": ["name", "pins"],
            },
        },
        "spis": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "pins": {
                        "type": "array",
                        "prefixItems": [
                            {"type": "integer"},
                            {"type": "integer"},
                            {"type": "integer"},
                            {"type": "integer"},
                        ],
                    },
                },
                "required": ["name", "pins"],
            },
        },
        "uarts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "pins": {
                        "type": "array",
                        "prefixItems": [
                            {"type": "integer"},
                            {"type": "integer"},
                        ],
                    },
                },
                "required": ["name", "pins"],
            },
        },
    },
    "required": ["available_channels", "digits", "pwms", "analogs"],
}
