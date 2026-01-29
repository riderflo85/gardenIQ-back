import re

STX = "<"
ETX = ">"

# Regular expression patterns for strict version strings
pattern_strict_version = re.compile(r"^\d{1,2}\.\d{1,2}\.\d{1,2}$")
# Regular expression pattern for received frame version strings from devices
pattern_recv_frame_version = re.compile(r"GDFW=\d{1,2}\.\d{1,2}\.\d{1,2}\s+MPFW=\d{1,2}\.\d{1,2}\.\d{1,2}")

# Je le met ici pour le moment pour ne pas oublier mais il faudra peut-être le déplacer plus tard !
# Define available fields by model to send with LG_INIT frame type.
fields_for_frame = {
    "Order": (
        "pk",
        "slug",
        "action_type",
        "arguments",
    ),
    "Argument": (
        "pk",
        "slug",
        "value_type",
        "required",
        "is_option",
    ),
}
