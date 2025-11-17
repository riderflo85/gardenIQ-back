import logging

from gardeniq.hardware.models import Device

from ..errors import CommandError
from ..errors import FrameProcessingError
from ..frame import Frame

logger = logging.getLogger(__name__)


class FrameHandler:

    def _get_device(self, uid: str) -> Device:
        try:
            device = Device.objects.get(uid=uid)
            return device
        except Device.DoesNotExist:
            logger.error(f"Device {uid} not found in database")
            raise FrameProcessingError(f"Unknown device: {uid}")

    def handle_device_response(self, frame: Frame) -> None:
        """
        Handle and process a response frame received from a device.

        This method processes frames sent by devices, performing validation checks
        and routing the frame to the appropriate handler based on its type.

        Args:
            frame (Frame): The frame object received from the device. Must have
                from_device=True.

        Raises:
            ValueError: If the frame is not from a device (from_device=False).
            ValueError: If the frame's checksum verification fails, indicating
                potential data corruption or security issues.

        Returns:
            None

        Note:
            The method performs the following operations in order:
            1. Validates that the frame originates from a device
            2. Verifies the frame's checksum for data integrity
            3. Checks for error responses and handles them appropriately
            4. Routes valid frames to specialized handlers based on frame type:
               - Ping responses
               - Order responses with data
               - Order responses without data
            5. Logs a warning for unrecognized frame types
        """
        if not frame.from_device:
            raise ValueError("Frame is not from device. Cannot execute.")

        # Verify checksum
        if not frame.verify_checksum():
            raise ValueError(
                f"Checksum verification failed for device {frame.device_uid}. " "Possible command jailbreak detected !"
            )

        # Handle errors
        if frame.has_response_error():
            self._handle_error_response(frame)
            return

        # Route to appropriate handler
        if frame.is_ping_response():
            self._handle_ping_response(frame)
        elif frame.is_order_response_with_data():
            self._handle_response_with_data(frame)
        elif frame.is_order_response_without_data():
            self._handle_response_without_data(frame)
        else:
            logger.warning(f"Unhandled frame type: {frame.frame_type}")

    def _handle_error_response(self, frame: Frame) -> None:
        logger.error(
            f"Device {frame.device_uid} returned error for command : "
            f"{frame.frame_type.value}|{frame.command_id}|{frame.command_slug}"
            f"{frame.err_msg.value if frame.err_msg else 'Unknow error'}"
        )

        # TODO: register the device error response into database telemetry
        #   OR/AND SSE system for display response state to user dashboard.
        if frame.err_msg is CommandError.TIMEOUT:
            device = self._get_device(frame.device_uid)
            device.mark_online(False)

    def _handle_ping_response(self, frame: Frame) -> None:
        device = self._get_device(frame.device_uid)
        device.mark_online()

        if frame.gd_fw_version and frame.mp_fw_version:
            device.set_firmware_versions(frame.gd_fw_version, frame.mp_fw_version)

    def _handle_response_with_data(self, frame: Frame) -> None:
        # TODO: register the device response data into log system
        #   OR database telemetry
        #   OR SSE system for display data to user dashboard.
        # e.g: back send `get_temp` order, device response with temp data.
        pass

    def _handle_response_without_data(self, frame: Frame) -> None:
        # TODO: register the device ok response state into log system
        #   OR database telemetry
        #   OR SSE system for display response state to user dashboard.
        # e.g: back send `open_van 1` order, device response without data. Juste state `ok` or `err`.
        pass
