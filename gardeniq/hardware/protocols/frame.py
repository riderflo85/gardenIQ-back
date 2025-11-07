from dataclasses import dataclass
from typing import List
from typing import Optional

from gardeniq.base.utils import GardenEnum

from .errors import CommandError
from .settings import pattern_recv_frame_version


class FrameType(GardenEnum):
    """Enumeration of frame types used by the communication protocol.

    Frame types:
    - CMD: Command frame — carries instructions or actions to be executed
    - PING: Keep-alive / heartbeat frame used to verify connectivity
    - ACK: Acknowledgement frame indicating successful receipt or processing
    """

    CMD = "CMD"
    PING = "PING"
    ACK = "ACK"


class CommandState(GardenEnum):
    OK = "OK"
    ERROR = "ERR"


@dataclass
class Frame:
    frame_type: FrameType
    device_uid: str
    command_id: int
    command_slug: str
    args_values: List[str]
    from_device: bool = False

    # Fields only present when from_device=True
    command_state: Optional[CommandState] = None  # State of the command on device
    ok_data: Optional[str] = None  # Data received from device when command sended is OK state
    err_msg: Optional[CommandError] = None  # Error message if cmd_state is ERROR
    gd_fw_version: Optional[str] = None  # GardenIQ Firmware Version
    mp_fw_version: Optional[str] = None  # MicroPython Firmware Version
    checksum: Optional[str] = None  # Checksum from device frame
    source_frame_from_device: Optional[str] = None  # Original frame string from device without \n

    def __post_init__(self):
        """
        Validate the frame data after initialization.

        This method is automatically called after the dataclass __init__ method.
        It ensures that if the frame is from a device, both the checksum and
        source_frame_from_device attributes are provided.

        Raises:
            ValueError: If from_device is True and checksum is None.
            ValueError: If from_device is True and source_frame_from_device is None.
        """
        if self.from_device:
            if self.checksum is None:
                raise ValueError("checksum must be provided if from_device is True")
            if self.source_frame_from_device is None:
                raise ValueError("source_frame_from_device must be provided if from_device is True")

    @staticmethod
    def build_checksum(data: bytes) -> int:
        """
        Calculate a Fletcher8 checksum for the given data.

        This function implements the Fletcher8 checksum algorithm, which computes
        a checksum value by maintaining two running sums of the input bytes.
        The two sums are then combined using bitwise operations to produce a
        single byte checksum value.

        Args:
            data (bytes): The input data for which to calculate the checksum.

        Returns:
            int: An 8-bit checksum value (0-255) computed using the Fletcher8 algorithm.

        Example:
            >>> checksum = build_checksum(b'hello')
            >>> isinstance(checksum, int)
            True
        """
        sum1 = 0
        sum2 = 0
        for b in data:
            sum1 = (sum1 + b) % 255
            sum2 = (sum2 + sum2) % 255
        return ((sum2 << 4) ^ sum1) & 0xFF

    def verify_checksum(self) -> bool:
        """
        Verify the Fletcher8 checksum for the frame.
        This method compares the checksum stored in the frame (self.cs) with a
        calculated checksum based on the source device frame data. The stored
        checksum is expected to be in hexadecimal format.

        Returns:
            bool: True if the calculated checksum matches the expected checksum,
                  False otherwise.
        """
        if (
            not self.from_device
            or not self.source_frame_from_device
            or not self.checksum
        ):
            return False

        # explain int(checksum_part, 16):
        # - Converts the hexadecimal string 'checksum_part' to an integer
        # - '16' indicates that the input string is in base 16 (hexadecimal)
        expected_checksum = int(self.checksum, 16)

        # Calculate the checksum for the data part
        calculated_checksum = self.build_checksum(self.source_frame_from_device.encode())
        return calculated_checksum == expected_checksum

    def is_ping_response(self) -> bool:
        if self.source_frame_from_device and pattern_recv_frame_version.match(self.source_frame_from_device):
            found_versions = True
        else:
            found_versions = False

        return (
            self.from_device
            and self.frame_type is FrameType.ACK
            and self.command_id == 0
            and found_versions
        )

    def _is_order_response(self) -> bool:
        return (
            self.from_device
            and self.frame_type is FrameType.ACK
            and self.command_id > 0
        )

    def is_order_response_with_data(self) -> bool:
        return self._is_order_response() and self.ok_data is not None

    def is_order_response_without_data(self) -> bool:
        return self._is_order_response() and self.ok_data is None

    def has_response_error(self) -> bool:
        return self.from_device and self.command_state is CommandState.ERROR
