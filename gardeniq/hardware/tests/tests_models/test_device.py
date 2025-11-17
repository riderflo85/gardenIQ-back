from enum import Enum

from django.conf import settings

import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Device


@pytest.fixture
def device_status(db):
    return Status.objects.create(name="Generic", tag="device-generic", color="#123456")


@pytest.fixture
def device(device_status):
    return Device.objects.create(
        name="Garden Sensor",
        description="Greenhouse sensor",
        uid="12AB34567890DEAD",
        path="/dev/ttyUSB0",
        status=device_status,
        gd_firmware_version="1.0.0",
        mp_firmware_version="1.0.0",
    )


@pytest.fixture(autouse=True)
def default_status_enum(settings):
    class DummyStatus(Enum):
        ONLINE = "En ligne"
        OFFLINE = "Hors ligne"

    settings.DEFAULT_STATUS = DummyStatus
    return DummyStatus


@pytest.fixture
def online_offline_statuses(db):
    online = Status.objects.create(
        name=settings.DEFAULT_STATUS.ONLINE.value,
        tag="device-online",
        color="#00FF00",
    )
    offline = Status.objects.create(
        name=settings.DEFAULT_STATUS.OFFLINE.value,
        tag="device-offline",
        color="#FF0000",
    )
    return {"online": online, "offline": offline}


@pytest.mark.django_db
class TestDeviceModel:

    def test_str_representation(self, device):
        # WHEN / THEN
        assert str(device) == "Device `Garden Sensor` : 12AB34567890DEAD : /dev/ttyUSB0"

    def test_check_update_returns_false_when_versions_missing(self, device):
        # GIVEN
        device.gd_firmware_version = ""

        # WHEN / THEN
        assert device._check_update() is False

    def test_check_update_detects_new_versions(self, device, mocker):
        # GIVEN
        mocker.patch("gardeniq.hardware.models.garden_firmware_version", "2.0.0")
        mocker.patch("gardeniq.hardware.models.micropython_version", "3.0.0")

        # WHEN / THEN
        assert device._check_update() is True

    def test_check_update_returns_false_when_up_to_date(self, device, mocker):
        # GIVEN
        mocker.patch("gardeniq.hardware.models.garden_firmware_version", device.gd_firmware_version)
        mocker.patch("gardeniq.hardware.models.micropython_version", device.mp_firmware_version)

        # WHEN / THEN
        assert device._check_update() is False

    def test_check_update_handles_version_errors(self, device, mocker):
        # GIVEN
        mocker.patch("gardeniq.hardware.models.Version", side_effect=ValueError("boom"))

        # WHEN / THEN
        assert device._check_update() is False

    def test_mark_online_sets_online_status(self, device, online_offline_statuses):
        # GIVEN
        device.status = online_offline_statuses["offline"]
        device.save()

        # WHEN
        device.mark_online()

        # THEN
        device.refresh_from_db()
        assert device.status == online_offline_statuses["online"]

    def test_mark_online_false_sets_offline_status(self, device, online_offline_statuses):
        # GIVEN
        device.status = online_offline_statuses["online"]
        device.save()

        # WHEN
        device.mark_online(on=False)

        # THEN
        device.refresh_from_db()
        assert device.status == online_offline_statuses["offline"]

    def test_set_firmware_versions_updates_fields_and_flag(self, device, mocker):
        # GIVEN
        new_versions = ("2.0.0", "3.0.0")
        check_mock = mocker.patch.object(device, "_check_update", return_value=True)
        save_mock = mocker.patch.object(device, "save")

        # WHEN
        device.set_firmware_versions(*new_versions)

        # THEN
        assert device.gd_firmware_version == new_versions[0]
        assert device.mp_firmware_version == new_versions[1]
        assert device.need_upgrade is True
        check_mock.assert_called_once_with()
        save_mock.assert_called_once_with()

    def test_set_firmware_versions_skips_save_when_not_changed(self, device, mocker):
        # GIVEN
        save_mock = mocker.patch.object(device, "save")
        check_mock = mocker.patch.object(device, "_check_update")

        # WHEN
        device.set_firmware_versions(device.gd_firmware_version, device.mp_firmware_version)

        # THEN
        save_mock.assert_not_called()
        check_mock.assert_not_called()
