from enum import Enum

__all__ = ["DefaultStatus"]


class DefaultStatus(Enum):
    ONLINE = "En ligne"
    OFFLINE = "Hors ligne"


# Register DefaultStatus class in a contante to call this class with django.conf.settings
DEFAULT_STATUS = DefaultStatus
