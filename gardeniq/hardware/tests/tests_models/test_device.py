from enum import Enum

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory


@pytest.fixture
def device_status(db):
    return Status.objects.create(name="Generic", tag="device-generic", color="#123456")


@pytest.fixture
def device(device_status, device_category):
    return Device.objects.create(
        name="Garden Sensor",
        description="Greenhouse sensor",
        uid="12AB34567890DEAD",
        path="/dev/ttyUSB0",
        status=device_status,
        category=device_category,
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
        mocker.patch("gardeniq.hardware.models.device.garden_firmware_version", "2.0.0")
        mocker.patch("gardeniq.hardware.models.device.micropython_version", "3.0.0")

        # WHEN / THEN
        assert device._check_update() is True

    def test_check_update_returns_false_when_up_to_date(self, device, mocker):
        # GIVEN
        mocker.patch("gardeniq.hardware.models.device.garden_firmware_version", device.gd_firmware_version)
        mocker.patch("gardeniq.hardware.models.device.micropython_version", device.mp_firmware_version)

        # WHEN / THEN
        assert device._check_update() is False

    def test_check_update_handles_version_errors(self, device, mocker):
        # GIVEN
        mocker.patch("gardeniq.hardware.models.device.Version", side_effect=ValueError("boom"))

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


VALID_PINS_CONFIGURATION = {
    "available_channels": ["digit", "analog"],
    "digits": [{"name": "GP0", "pins": [0]}],
    "pwms": [{"name": "PWM0", "pins": [0]}],
    "analogs": [{"name": "ADC0", "pins": [26]}],
}


@pytest.fixture
def device_category(db):
    return DeviceCategory.objects.create(name="Raspberry Pi Pico", pins_configuration=VALID_PINS_CONFIGURATION)


@pytest.mark.django_db
class TestDeviceCategoryModel:

    def test_str_representation(self, device_category):
        """The string representation shows the category name."""
        # WHEN / THEN
        assert str(device_category) == "DeviceCategory `Raspberry Pi Pico`"

    def test_default_values(self, device_category):
        """A category created without seeder fields is ready, without seed_id nor description."""
        # WHEN / THEN
        assert device_category.is_ready is True
        assert device_category.seed_id is None
        assert device_category.description == ""

    def test_save_rejects_pins_configuration_missing_required_key(self, db):
        """Saving a pins_configuration without a required key raises a ValidationError on this field."""
        # GIVEN
        pins_configuration = {k: v for k, v in VALID_PINS_CONFIGURATION.items() if k != "digits"}

        # WHEN / THEN
        with pytest.raises(ValidationError) as exc_info:
            DeviceCategory.objects.create(name="Bad", pins_configuration=pins_configuration)
        assert "pins_configuration" in exc_info.value.message_dict
        assert DeviceCategory.objects.count() == 0

    def test_save_rejects_missing_pins_configuration(self, db):
        """A category without pins_configuration is refused."""
        # WHEN / THEN
        with pytest.raises(ValidationError):
            DeviceCategory.objects.create(name="Empty")

    def test_save_rejects_pin_entry_without_pins(self, db):
        """A pin entry without its `pins` list is refused."""
        # GIVEN
        pins_configuration = {**VALID_PINS_CONFIGURATION, "digits": [{"name": "GP0"}]}

        # WHEN / THEN
        with pytest.raises(ValidationError):
            DeviceCategory.objects.create(name="Bad", pins_configuration=pins_configuration)

    def test_save_validates_on_update(self, device_category):
        """An existing category cannot be saved with an invalid pins_configuration."""
        # GIVEN
        device_category.pins_configuration = {"available_channels": "digit"}

        # WHEN / THEN
        with pytest.raises(ValidationError):
            device_category.save()
        device_category.refresh_from_db()
        assert device_category.pins_configuration == VALID_PINS_CONFIGURATION

    def test_delete_protected_when_used_by_device(self, device_category, device_status):
        """A category used by a device cannot be deleted (on_delete=PROTECT)."""
        # GIVEN
        Device.objects.create(name="Card", uid="AABBCCDDEEFF0011", category=device_category, status=device_status)

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            device_category.delete()
        assert DeviceCategory.objects.filter(pk=device_category.pk).exists()

    def test_devices_related_name(self, device_category, device_status):
        """Devices of a category are reachable through `devices`."""
        # GIVEN
        device = Device.objects.create(
            name="Card", uid="AABBCCDDEEFF0011", category=device_category, status=device_status
        )

        # WHEN / THEN
        assert list(device_category.devices.all()) == [device]
