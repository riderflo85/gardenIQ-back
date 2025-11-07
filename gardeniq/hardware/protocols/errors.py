from gardeniq.base.utils import GardenEnum


class FrameParsingError(Exception):
    """Raised when frame parsing fails."""
    pass


class FrameProcessingError(Exception):
    """Raised when frame processing fails."""
    pass


class CommandError(GardenEnum):
    """
    Enumeration of possible command execution errors.

    This enum defines the various error states that can occur during command
    processing and communication with hardware devices.

    Attributes:
        UNKNOW_CMD: Command identifier is not recognized or does not exist
        INVALID_PARAM: Command parameters are malformed or invalid
        TIMEOUT: Device failed to respond within the expected time frame
        BUSY: Device is currently processing another operation
        CHECKSUM_ERR: Data integrity check failed, indicating potential data corruption
        DEV_NOT_READY: Device is not in a state to accept or execute commands
    """
    UNKNOW_CMD = "UNKNOW_CMD"
    INVALID_PARAM = "INVALID_PARAM"
    TIMEOUT = "TIMEOUT"
    BUSY = "BUSY"
    CHECKSUM_ERR = "CHECKSUM_ERR"
    DEV_NOT_READY = "DEV_NOT_READY"
