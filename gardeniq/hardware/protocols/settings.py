import re

STX = "<"
ETX = ">"

# Regular expression patterns for strict version strings
pattern_strict_version = re.compile(r"^\d{1,2}\.\d{1,2}\.\d{1,2}$")
# Regular expression pattern for received frame version strings from devices
pattern_recv_frame_version = re.compile(r"GDFW=\d{1,2}\.\d{1,2}\.\d{1,2}\s+MPFW=\d{1,2}\.\d{1,2}\.\d{1,2}")
