import re
from enum import Enum

__all__ = [
    "BAUDRATE",
    "LD_FORMATS",
    "PATTERN_SERIAL_PORT",
    "DATASHEET_JSON_SCHEMA",
    "PIN_INIT_CONFIG_JSON_SCHEMA",
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


def _channels_schema(pin_count: int) -> dict[str, object]:
    """
    Build the JSON schema of a list of channels: [{"name": "...", "pins": [<int>, ...]}, ...].

    "prefixItems" is positional: the n-th pin must match the n-th schema of the list, so repeating the
    integer schema `pin_count` times describes a channel wired to `pin_count` integer pins.
    It only checks the listed positions: it does not force the number of pins and does not type extra ones.
    """
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "pins": {"type": "array", "prefixItems": [{"type": "integer"}] * pin_count},
            },
            "required": ["name", "pins"],
        },
    }


# Datasheet of a card: the names of its available channels and, per channel type, the channels with their pins.
# i2cs and uarts use 2 pins per channel, spis 4 and the other types 1. i2cs, spis and uarts are optional.
DATASHEET_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "available_channels": {"type": "array", "items": {"type": "string"}},
        "digits": _channels_schema(1),
        "pwms": _channels_schema(1),
        "analogs": _channels_schema(1),
        "i2cs": _channels_schema(2),
        "spis": _channels_schema(4),
        "uarts": _channels_schema(2),
    },
    "required": ["available_channels", "digits", "pwms", "analogs"],
}

# Schema of the pin_init_cfg field: how to instantiate the MicroPython object that controls a pin.
# "c" > channel_class. Is a string to represent the MicroPython class to control pin. It must be in the firmware
#       whitelist (MP_MACHINE): a new class needs a firmware update and a new entry in the enum below.
# "a" > channel_args. Is a dictionary to represent the arguments to initialize the MicroPython class, as
#       {"argument name": value}. The names are not listed on purpose: a MicroPython update (new or renamed
#       argument) needs no change here.
# A value is "@pin" (the pin number, Pin.pin_number), "@:NAME" (constant NAME of the class "c", e.g. "@:IN" with
# "c": "Pin" is machine.Pin.IN) or a literal sent as is.
# e.g. {"c": "PWM", "a": {"dest": "@pin", "freq": 1000, "duty_u16": 512}} represents a PWM channel with
# frequency 1000 Hz and duty cycle 512.
PIN_INIT_CONFIG_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "c": {"enum": ["PWM", "Pin", "ADC"]},
        "a": {
            "type": "object",
            # propertyNames checks the argument names, additionalProperties checks their values.
            "propertyNames": {"$ref": "#/$defs/frame_safe"},
            "additionalProperties": {"$ref": "#/$defs/arg_value"},
            # At least one argument is the pin number. JSON Schema has no "some value equals X" for an object,
            # so this reads "not (every value differs from @pin)". The error message describes that negation.
            "not": {"additionalProperties": {"not": {"const": "@pin"}}},
        },
    },
    "required": ["c", "a"],
    # Only "c" and "a": a new format is a protocol change, not a looser schema.
    "additionalProperties": False,
    # "$defs" only stores named sub-schemas, applied where a "$ref" points at them.
    "$defs": {
        # A space or ";" in a string breaks the USB frame (they separate blocks and fields).
        # "pattern" is not anchored: it means "contains". "not" flips it, and needs "type": "string" because
        # "pattern" ignores other types and "not" would then reject numbers. It replaces "^[^\\s;]*$" since
        # "$" also matches before a trailing "\n".
        "frame_safe": {"not": {"type": "string", "pattern": "[\\s;]"}},
        # Any JSON value whose strings, keys included, are frame safe, at any depth (it calls itself).
        # Each keyword only applies to its own type; numbers, booleans and null match none and pass.
        "literal": {
            "$ref": "#/$defs/frame_safe",  # strings
            "items": {"$ref": "#/$defs/literal"},  # arrays
            "propertyNames": {"$ref": "#/$defs/frame_safe"},  # objects: the keys...
            "additionalProperties": {"$ref": "#/$defs/literal"},  # ...and the values
        },
        # Top-level values of "a". A string starting with "@" is a reference and only "@pin" and "@:NAME" (upper
        # case) exist. Nested strings are not interpreted by the firmware, so they stay a plain "literal".
        "arg_value": {
            "$ref": "#/$defs/literal",
            "if": {"type": "string", "pattern": "^@"},
            "then": {"pattern": "^@(pin|:[A-Z][A-Z0-9_]*)$"},
        },
    },
}
