import pytest

from gardeniq.hardware.protocols.frame import CommandState
from gardeniq.hardware.protocols.frame import Frame
from gardeniq.hardware.protocols.frame import FrameType


@pytest.fixture
def device_frame_factory():
    """Return a helper to build fully populated device frames for tests."""
    base_source_frame = "GDFW=1.2.3 MPFW=4.5.6"
    base_checksum = f"{Frame.build_checksum(base_source_frame.encode()):02X}"

    def _factory(**overrides):
        data = {
            "frame_type": FrameType.ACK,
            "device_uid": "DEV-001",
            "command_id": 0,
            "command_slug": "ping",
            "args_values": [],
            "from_device": True,
            "checksum": base_checksum,
            "source_frame_from_device": base_source_frame,
            "command_state": CommandState.OK,
            "ok_data": None,
        }
        data.update(overrides)
        return data

    return _factory


class TestFrameModel:
    def test_frame_from_device_requires_checksum(self):
        # GIVEN / WHEN / THEN
        with pytest.raises(ValueError, match="checksum must be provided"):
            Frame(
                frame_type=FrameType.ACK,
                device_uid="DEV-001",
                command_id=0,
                command_slug="ping",
                args_values=[],
                from_device=True,
                source_frame_from_device="ACK 0",
            )

    def test_frame_from_device_requires_source_frame(self):
        # GIVEN / WHEN / THEN
        with pytest.raises(ValueError, match="source_frame_from_device must be provided"):
            Frame(
                frame_type=FrameType.ACK,
                device_uid="DEV-001",
                command_id=0,
                command_slug="ping",
                args_values=[],
                from_device=True,
                checksum="AA",
            )

    def test_verify_checksum_with_matching_value(self, device_frame_factory):
        # GIVEN
        frame = Frame(**device_frame_factory())

        # WHEN / THEN
        assert frame.verify_checksum() is True

    def test_verify_checksum_returns_false_with_mismatch(self, device_frame_factory):
        # GIVEN
        frame = Frame(**device_frame_factory(checksum="00"))

        # WHEN / THEN
        assert frame.verify_checksum() is False

    def test_is_ping_response_detects_device_versions(self, device_frame_factory):
        # GIVEN
        frame = Frame(**device_frame_factory())

        # WHEN / THEN
        assert frame.is_ping_response() is True

    def test_is_ping_response_false_without_version_string(self, device_frame_factory):
        # GIVEN
        frame = Frame(**device_frame_factory(source_frame_from_device="ACK 0 PING"))

        # WHEN / THEN
        assert frame.is_ping_response() is False

    def test_is_order_response_with_data(self, device_frame_factory):
        # GIVEN
        frame = Frame(**device_frame_factory(command_id=42, ok_data="sensor=42", command_slug="status"))

        # WHEN / THEN
        assert frame.is_order_response_with_data() is True
        assert frame.is_order_response_without_data() is False

    def test_is_order_response_without_data(self, device_frame_factory):
        # GIVEN
        frame = Frame(**device_frame_factory(command_id=7, ok_data=None, command_slug="status"))

        # WHEN / THEN
        assert frame.is_order_response_without_data() is True
        assert frame.is_order_response_with_data() is False

    def test_has_response_error(self, device_frame_factory):
        # GIVEN
        frame = Frame(**device_frame_factory(command_state=CommandState.ERROR))

        # WHEN / THEN
        assert frame.has_response_error() is True
