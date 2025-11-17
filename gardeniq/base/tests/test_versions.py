from django.core.exceptions import ValidationError

import pytest

from gardeniq.__version__ import Version
from gardeniq.__version__ import get_gd_fw_version
from gardeniq.__version__ import get_micropython_version


@pytest.fixture
def config_value_mock(mocker):
    return mocker.patch("gardeniq.__version__.get_config_value")


@pytest.fixture
def request_version_mock(mocker):
    return mocker.patch("gardeniq.__version__.request_repot_version")


def test_version_ordering_and_equality():
    first = Version("1.2.3")
    second = Version("1.2.4")
    third = Version("2.0.0")

    assert first == Version("1.2.3")
    assert first < second < third
    assert repr(first) == "Version 1.2.3"


def test_version_rejects_invalid_string():
    with pytest.raises(ValidationError):
        Version("1.2")


def test_version_compared_to_non_version_raises():
    with pytest.raises(NotImplementedError):
        _ = Version("1.0.0") == "1.0.0"


def test_get_micropython_version_uses_config_and_request(config_value_mock, request_version_mock):
    expected_url = "https://api.test/micropython"
    config_value_mock.return_value = expected_url
    request_version_mock.return_value = "1.1.1"

    result = get_micropython_version()

    config_value_mock.assert_called_once_with("micropython_repot", default="", cast=str)
    request_version_mock.assert_called_once_with(expected_url)
    assert result == "1.1.1"


def test_get_gd_fw_version_uses_config_and_request(config_value_mock, request_version_mock):
    expected_url = "https://api.test/gdfw"
    config_value_mock.return_value = expected_url
    request_version_mock.return_value = "2.2.2"

    result = get_gd_fw_version()

    config_value_mock.assert_called_once_with("gardeniq_firmware_repot", default="", cast=str)
    request_version_mock.assert_called_once_with(expected_url)
    assert result == "2.2.2"
