from ..errors import FrameParsingError
from ..frame import CommandError
from ..frame import CommandState
from ..frame import Frame
from ..frame import FrameType
from ..settings import ETX
from ..settings import STX
from ..settings import pattern_recv_frame_version


class FrameParser:
    """
    Parser for communication frames between the system and hardware devices.

    This class provides static methods to parse frame strings received from hardware devices
    into structured Frame objects. It validates frame format, extracts components, and handles
    different command states and response types.
    This class is responsible for parsing and validation only.
    It does NOT access the database or perform any business logic.
    """

    @staticmethod
    def parse_from_device(recv_str: str) -> Frame:
        """
        Parse a frame string received from a device into a Frame object.

        This method parses a newline-terminated string from a device and extracts all frame components
        including frame type, device UID, command ID, command state, and optional data fields such as
        firmware versions or error messages.

        Args:
            recv_str (str): The raw string received from the device. Must end with a newline character.
                        Expected format: "STX frame_type device_uid command_id command_state [data...] ETX checksum\n"

        Returns:
            Frame: A Frame object containing all parsed components from the received string.

        Raises:
            ValueError: If the received string does not end with a newline character.
            ValueError: If the received string has fewer than 7 parts (minimum valid frame).
            ValueError: If STX or ETX markers are invalid.
            ValueError: If the frame type cannot be parsed.
            ValueError: If the command state is invalid.
            ValueError: If command state is ERROR but the error message cannot be parsed.

        Notes:
            - When command_state is ERROR, the method expects an error message in parts[5].
            - When command_state is OK and command_id > 0, parts[5] contains response data.
            - When command_state is OK and command_id == 0 (PING response), firmware versions
              are extracted from parts[5] and parts[6] if they match the expected pattern.
            - The returned Frame object has from_device=True and does not include command_slug
              or args_values as these are not present in device responses.
        """
        if not recv_str.endswith("\n"):
            raise FrameParsingError("The received string does not end with a newline character. It's invalid frame !")

        recv_str = recv_str.removesuffix("\n")
        parts = recv_str.split(" ")

        if len(parts) < 7:
            raise FrameParsingError(
                f"The received string is too short. Warning: the system may be infected. recv: {recv_str}"
            )

        # Extract and validate basic components
        stx = parts[0]
        etx = parts[-2]
        checksum = parts[-1]

        if stx != STX:
            raise FrameParsingError(f"Invalid STX in received frame. Received: {stx}")
        if etx != ETX:
            raise FrameParsingError(f"Invalid ETX in received frame. Received: {etx}")

        # Parse frame type
        frame_type_obj = FrameType.from_string(parts[1])
        if not frame_type_obj:
            raise FrameParsingError(f"Invalid frame type in received frame. Received: {parts[1]}")

        # Extract device UID and command ID
        device_uid = parts[2]
        command_id = int(parts[3])
        # command_obj = Order.objects.get(pk=cmd_id) if cmd_id > 0 else 0

        # Parse command state
        command_state = CommandState.from_string(parts[4])
        if not command_state:
            raise FrameParsingError(f"Invalid command state in received frame. Received: {parts[4]}")

        # Parse conditional data based on command state
        ok_data = None
        error_msg = None
        garden_firmware_version = None
        micro_python_firmware_version = None

        if command_state is CommandState.ERROR:
            error_msg = CommandError.from_string(parts[5])
            if not error_msg:
                raise FrameParsingError(f"Invalid command error in received frame. Received: {parts[5]}")
        elif command_state is CommandState.OK:
            if command_id > 0:
                # Classic order response (e.g, : response to get_temp order return temp)
                ok_data = parts[5]
            else:
                # PING response with firmware versions
                if pattern_recv_frame_version.match(recv_str):
                    # GDFW=XX.XX.XX -> XX.XX.XX
                    garden_firmware_version = parts[5].split("=")[-1]
                    # MPFW=XX.XX.XX -> XX.XX.XX
                    micro_python_firmware_version = parts[6].split("=")[-1]

        return Frame(
            frame_type=frame_type_obj,
            device_uid=device_uid,
            command_id=command_id,
            command_slug="",  # Not present in device responses
            args_values=[],  # Not present in device responses
            from_device=True,
            command_state=command_state,
            ok_data=ok_data,
            err_msg=error_msg,
            gd_fw_version=garden_firmware_version,
            mp_fw_version=micro_python_firmware_version,
            checksum=checksum,
            source_frame_from_device=recv_str,
        )

    @staticmethod
    def parse_from_frame_klass(frame_obj: Frame) -> str:
        """
        Serialize a Frame object into a string representation for transmission.

        This method converts a Frame object into a properly formatted string that can be
        sent to a device, including STX/ETX markers and a checksum for data integrity.

        Args:
            frame_obj (Frame): The Frame object to serialize. Must not be a device-originated frame.

        Returns:
            str: A formatted frame string with the following structure:
                "<STX> <frame_type> <device_uid> [conditional_part] <ETX> <checksum>\n"
                where:
                - STX/ETX are start/end transmission markers
                - conditional_part depends on frame_type and command_id
                - checksum is a 2-digit uppercase hexadecimal value

        Raises:
            FrameParsingError: If frame_obj.from_device is True, as device frames
                              cannot be serialized using this method.

        Note:
            The conditional frame part varies based on frame type:
            - CMD with command_id > 0 and command_slug: "command_id command_slug args"
            - CMD with command_id > 0 (no slug): "command_id args"
            - PING: "0"
            - Other types: empty string
        """
        if frame_obj.from_device:
            raise FrameParsingError("Cannot build frame from device frame.")

        # Build conditional frame part based on type
        match (frame_obj.frame_type, frame_obj.command_id, frame_obj.command_slug):
            # pk = PrimaryKey of Order object model
            case (FrameType.CMD, pk, slug) if pk > 0 and slug != "":
                args_str = ",".join(frame_obj.args_values)
                conditionnal_frame = f"{pk} {slug} {args_str}"
            case (FrameType.CMD, pk, _) if pk > 0:
                args_str = ",".join(frame_obj.args_values)
                conditionnal_frame = f"{pk} {args_str}"
            case (FrameType.PING, _, _):
                conditionnal_frame = "0"
            case (_, _, _):
                conditionnal_frame = ""

        # Build complete frame
        frame_str = f"{STX} {frame_obj.frame_type.value} {frame_obj.device_uid} {conditionnal_frame} {ETX}"
        checksum = Frame.build_checksum(frame_str.encode())

        # explain f"{checksum:02X} formatting:
        # - f"..." indicates an f-string, allowing inline expressions
        # - {checksum:02X} formats 'checksum' as a hexadecimal string
        #   - 0: pad with leading zeros if necessary
        #   - 2: ensure at least 2 characters wide
        #   - X: use uppercase hexadecimal digits (A-F)
        return f"{frame_str} {checksum:02X}\n"
