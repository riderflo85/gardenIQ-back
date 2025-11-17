import pytest

import gardeniq.hardware.protocols.usb.parser as parser_module
from gardeniq.hardware.protocols.errors import CommandError
from gardeniq.hardware.protocols.errors import FrameParsingError
from gardeniq.hardware.protocols.frame import CommandState
from gardeniq.hardware.protocols.frame import Frame
from gardeniq.hardware.protocols.frame import FrameType
from gardeniq.hardware.protocols.settings import ETX
from gardeniq.hardware.protocols.settings import STX
from gardeniq.hardware.protocols.usb import FrameParser


@pytest.fixture
def version_pattern_stub(monkeypatch):
    """Patch firmware regex pattern so we can force match outcomes."""

    class _PatternStub:
        def __init__(self):
            self.should_match = True
            self.calls = []

        def match(self, value: str):
            self.calls.append(value)
            return self.should_match

    stub = _PatternStub()
    monkeypatch.setattr(parser_module, "pattern_recv_frame_version", stub)
    return stub


class TestFrameParser:
    def test_parse_from_device_ok_response_returns_data(self):
        # GIVEN
        recv = f"{STX} ACK device-42 7 OK 24.5C {ETX} 00\n"

        # WHEN
        frame = FrameParser.parse_from_device(recv)

        # THEN
        assert frame.from_device is True
        assert frame.device_uid == "device-42"
        assert frame.command_id == 7
        assert frame.command_state is CommandState.OK
        assert frame.ok_data == "24.5C"
        assert frame.err_msg is None

    def test_parse_from_device_error_response_sets_command_error(self):
        # GIVEN
        recv = f"{STX} ACK device-99 3 ERR {CommandError.UNKNOW_CMD.value} {ETX} AA\n"

        # WHEN
        frame = FrameParser.parse_from_device(recv)

        # THEN
        assert frame.command_state is CommandState.ERROR
        assert frame.err_msg is CommandError.UNKNOW_CMD
        assert frame.ok_data is None

    def test_parse_from_device_ping_response_extracts_versions(self, version_pattern_stub):
        version_pattern_stub.should_match = True
        # GIVEN
        recv = f"{STX} ACK hw-01 0 OK GDFW=1.2.3 MPFW=4.5.6 {ETX} FF\n"

        # WHEN
        frame = FrameParser.parse_from_device(recv)

        # THEN
        assert frame.command_state is CommandState.OK
        assert frame.gd_fw_version == "1.2.3"
        assert frame.mp_fw_version == "4.5.6"
        assert version_pattern_stub.calls == [recv.removesuffix("\n")]

    def test_parse_from_device_requires_newline(self):
        # GIVEN
        recv = f"{STX} ACK device-42 7 OK 24.5C {ETX} 00"

        # WHEN / THEN
        with pytest.raises(FrameParsingError, match="newline"):
            FrameParser.parse_from_device(recv)

    def test_parse_from_frame_klass_cmd_with_slug(self):
        # GIVEN
        frame_obj = Frame(
            frame_type=FrameType.CMD,
            device_uid="garden-01",
            command_id=9,
            command_slug="set_temp",
            args_values=["21", "C"],
        )

        # WHEN
        built = FrameParser.parse_from_frame_klass(frame_obj)

        # THEN
        conditional = f"{frame_obj.command_id} {frame_obj.command_slug} {','.join(frame_obj.args_values)}"
        expected_frame = f"{STX} {frame_obj.frame_type.value} {frame_obj.device_uid} {conditional} {ETX}"
        expected_checksum = Frame.build_checksum(expected_frame.encode())
        assert built == f"{expected_frame} {expected_checksum:02X}\n"

    def test_parse_from_frame_klass_rejects_device_frame(self):
        # GIVEN
        source = f"{STX} ACK device-1 0 OK GDFW=1.0.0 MPFW=1.0.0 {ETX} 00"
        frame_obj = Frame(
            frame_type=FrameType.ACK,
            device_uid="device-1",
            command_id=0,
            command_slug="",
            args_values=[],
            from_device=True,
            command_state=CommandState.OK,
            checksum="00",
            source_frame_from_device=source,
        )

        # WHEN / THEN
        with pytest.raises(FrameParsingError, match="Cannot build frame from device frame."):
            FrameParser.parse_from_frame_klass(frame_obj)
