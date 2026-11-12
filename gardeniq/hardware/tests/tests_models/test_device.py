import logging
from enum import Enum

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.db.models import ProtectedError
from django.db.models import QuerySet

import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.fixtures.seeders import ChannelSeeder
from gardeniq.hardware.fixtures.seeders import DeviceCategorySeeder
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.models import Pin


@pytest.fixture
def device_status(db):
    return Status.objects.create(name="Generic", tag="device-generic", color="#123456")


@pytest.fixture
def channels(db):
    """Create the channels the datasheets of these tests list: saving a device creates its pins from them."""
    return {name: Channel.objects.create(name=name) for name in ("digit", "analog", "pwm", "i2c")}


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


@pytest.mark.django_db
class TestDeviceUid:

    def test_uid_defaults_to_none(self, device_status, device_category):
        """A device created without uid stores NULL, not an empty string."""
        # GIVEN / WHEN
        device = Device.objects.create(name="Card", category=device_category, status=device_status)

        # THEN
        device.refresh_from_db()
        assert device.uid is None

    def test_several_devices_without_uid_are_allowed(self, device_status, device_category):
        """Several devices without uid do not break the uniqueness of uid."""
        # GIVEN
        Device.objects.create(name="Card 1", category=device_category, status=device_status)

        # WHEN
        Device.objects.create(name="Card 2", category=device_category, status=device_status)

        # THEN
        assert Device.objects.filter(uid__isnull=True).count() == 2

    def test_uid_is_unique_when_set(self, device_status, device_category):
        """Two devices cannot share the same uid."""
        # GIVEN
        Device.objects.create(name="Card 1", uid="12AB34567890DEAD", category=device_category, status=device_status)

        # WHEN / THEN
        with pytest.raises(IntegrityError), transaction.atomic():
            Device.objects.create(name="Card 2", uid="12AB34567890DEAD", category=device_category, status=device_status)


VALID_PINS_CONFIGURATION = {
    "available_channels": ["digit", "analog"],
    "digits": [{"name": "GP0", "pins": [0]}],
    "pwms": [{"name": "PWM0", "pins": [0]}],
    "analogs": [{"name": "ADC0", "pins": [26]}],
}


@pytest.fixture
def device_category(channels):
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

    def test_full_clean_rejects_invalid_pins_configuration(self, db):
        """full_clean() reports an invalid pins_configuration on this field, as model forms (admin) need."""
        # GIVEN
        category = DeviceCategory(name="Bad", pins_configuration={"available_channels": "digit"})

        # WHEN / THEN
        with pytest.raises(ValidationError) as exc_info:
            category.full_clean()
        assert list(exc_info.value.message_dict) == ["pins_configuration"]

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


DATASHEET = {
    "available_channels": ["digit", "analog", "pwm"],
    "digits": [{"name": "GP0", "pins": [0]}, {"name": "GP26", "pins": [26]}],
    "pwms": [{"name": "PWM0", "pins": [0]}],
    "analogs": [{"name": "ADC0", "pins": [26]}],
}

EMPTY_DATASHEET = {"available_channels": [], "digits": [], "pwms": [], "analogs": []}


def available_channels_by_pin(device):
    """Return {pin_number: sorted names of its available channels} for the pins of a device."""
    return {
        pin.pin_number: sorted(channel.name for channel in pin.channels_available.all())
        for pin in Pin.objects.filter(device=device)
    }


@pytest.mark.django_db
class TestDeviceCreatePinsWithDatasheet:

    @pytest.fixture
    def create_device(self, device_status):
        """
        Return a function that creates a device whose category holds the given datasheet.

        `save()` creates the pins of a new device, so the device is saved with an empty datasheet (no pin) and the
        datasheet under test is only assigned afterwards: each test then calls `_create_pins_with_datasheet()` itself.
        """

        def _create_device(pins_configuration, uid="AABBCCDDEEFF0011"):
            empty_category = DeviceCategory.objects.create(name=f"Empty {uid}", pins_configuration=EMPTY_DATASHEET)
            device = Device.objects.create(name=f"Card {uid}", uid=uid, category=empty_category, status=device_status)
            device.category = DeviceCategory.objects.create(
                name=f"Category {uid}", pins_configuration=pins_configuration
            )
            return device

        return _create_device

    def test_creates_one_pin_per_pin_number_with_its_available_channels(self, channels, create_device):
        """Each pin number of the datasheet becomes a Pin, available on the channels that list it."""
        # GIVEN
        device = create_device(DATASHEET)

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        assert available_channels_by_pin(device) == {0: ["digit", "pwm"], 26: ["analog", "digit"]}

    def test_leaves_channel_choiced_empty(self, channels, create_device):
        """The channel of a created pin is chosen later: channel_choiced stays empty."""
        # GIVEN
        device = create_device(DATASHEET)

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        assert Pin.objects.filter(device=device).count() == 2
        assert not Pin.objects.filter(device=device, channel_choiced__isnull=False).exists()

    def test_does_not_create_pins_for_other_devices(self, channels, create_device):
        """Only the pins of the device on which the method runs are created."""
        # GIVEN
        device = create_device(DATASHEET)
        other_device = create_device(DATASHEET, uid="1122334455667788")

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        assert Pin.objects.filter(device=device).exists()
        assert not Pin.objects.filter(device=other_device).exists()

    def test_ignores_channels_missing_from_available_channels(self, channels, create_device):
        """A channel type that is not in available_channels is ignored, even if the datasheet lists pins for it."""
        # GIVEN
        pins_configuration = {**DATASHEET, "available_channels": ["digit"], "pwms": [{"name": "PWM5", "pins": [5]}]}
        device = create_device(pins_configuration)

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        assert available_channels_by_pin(device) == {0: ["digit"], 26: ["digit"]}

    def test_every_pin_of_a_multi_pin_channel_gets_the_channel(self, channels, create_device):
        """A channel wired to several pins (I2C: SDA and SCL) is available on each of them."""
        # GIVEN
        pins_configuration = {**DATASHEET, "available_channels": ["i2c"], "i2cs": [{"name": "I2C0", "pins": [0, 1]}]}
        device = create_device(pins_configuration)

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        assert available_channels_by_pin(device) == {0: ["i2c"], 1: ["i2c"]}

    def test_pin_listed_several_times_for_a_channel_gets_it_once(self, channels, create_device):
        """A pin repeated in the datasheet for the same channel type is linked to that channel only once."""
        # GIVEN
        pins_configuration = {
            **DATASHEET,
            "available_channels": ["digit"],
            "digits": [{"name": "GP26", "pins": [26, 26]}, {"name": "GP26 bis", "pins": [26]}],
        }
        device = create_device(pins_configuration)

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        assert available_channels_by_pin(device) == {26: ["digit"]}

    @pytest.mark.parametrize(
        "pins_configuration",
        [
            {"available_channels": [], "digits": [], "pwms": [], "analogs": []},
            {"available_channels": ["digit"], "digits": [], "pwms": [], "analogs": []},
        ],
        ids=["no-channel", "channel-without-pin"],
    )
    def test_creates_nothing_when_datasheet_lists_no_pin(self, channels, create_device, pins_configuration):
        """A datasheet without any pin to create leaves the device without pins."""
        # GIVEN
        device = create_device(pins_configuration)

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        assert not Pin.objects.exists()

    def test_second_run_gives_the_same_pins(self, channels, create_device):
        """Running the method again keeps the same pins and links, without error."""
        # GIVEN
        device = create_device(DATASHEET)
        device._create_pins_with_datasheet()
        pin_ids = set(Pin.objects.filter(device=device).values_list("pk", flat=True))

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        assert set(Pin.objects.filter(device=device).values_list("pk", flat=True)) == pin_ids
        assert available_channels_by_pin(device) == {0: ["digit", "pwm"], 26: ["analog", "digit"]}

    def test_existing_pin_is_reused_and_its_channels_refreshed(self, channels, create_device):
        """A pin already created is kept, with its chosen channel, and gets the channels of the datasheet."""
        # GIVEN
        device = create_device(DATASHEET)
        existing_pin = Pin.objects.create(device=device, pin_number=26, channel_choiced=channels["digit"])
        existing_pin.channels_available.set([channels["pwm"]])

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        refreshed_pin = Pin.objects.get(device=device, pin_number=26)
        assert refreshed_pin.pk == existing_pin.pk
        assert refreshed_pin.channel_choiced == channels["digit"]
        assert available_channels_by_pin(device)[26] == ["analog", "digit"]

    def test_pin_missing_from_datasheet_is_left_untouched(self, channels, create_device):
        """A pin of the device that the datasheet does not list is neither deleted nor changed."""
        # GIVEN
        device = create_device(DATASHEET)
        extra_pin = Pin.objects.create(device=device, pin_number=99)
        extra_pin.channels_available.set([channels["pwm"]])

        # WHEN
        device._create_pins_with_datasheet()

        # THEN
        assert available_channels_by_pin(device) == {0: ["digit", "pwm"], 26: ["analog", "digit"], 99: ["pwm"]}

    def test_raises_when_a_channel_is_not_in_database(self, create_device, caplog):
        """A channel of available_channels that is not in the database is an error, not a channel to create."""
        # GIVEN
        Channel.objects.create(name="digit")
        device = create_device(DATASHEET)

        # WHEN / THEN
        with caplog.at_level(logging.WARNING, logger="gardeniq.hardware.models.device"):
            with pytest.raises(Channel.DoesNotExist) as exc_info:
                device._create_pins_with_datasheet()
        assert "['analog', 'pwm']" in str(exc_info.value)
        assert str(device.category) in str(exc_info.value)
        assert Channel.objects.count() == 1
        assert not Pin.objects.exists()
        assert [record.getMessage() for record in caplog.records] == [str(exc_info.value)]

    def test_writes_nothing_when_a_step_fails(self, channels, create_device, mocker):
        """A failure after the pins are created rolls them back: the method runs in one transaction."""
        # GIVEN
        device = create_device(DATASHEET)
        real_bulk_create = QuerySet.bulk_create
        calls = []

        def fail_on_second_call(queryset, objs, *args, **kwargs):
            calls.append(queryset.model)
            if len(calls) == 2:
                raise RuntimeError("boom")
            return real_bulk_create(queryset, objs, *args, **kwargs)

        mocker.patch.object(QuerySet, "bulk_create", fail_on_second_call)

        # WHEN / THEN
        with pytest.raises(RuntimeError, match="boom"):
            device._create_pins_with_datasheet()
        assert len(calls) == 2
        assert not Pin.objects.exists()


@pytest.mark.django_db
class TestDeviceSave:

    @pytest.fixture
    def category(self, db):
        return DeviceCategory.objects.create(name="Category", pins_configuration=DATASHEET)

    def test_creation_creates_the_pins_of_the_datasheet(self, channels, category, device_status):
        """Creating a device creates the pins listed in the datasheet of its category."""
        # GIVEN / WHEN
        device = Device.objects.create(name="Card", uid="AABBCCDDEEFF0011", category=category, status=device_status)

        # THEN
        assert available_channels_by_pin(device) == {0: ["digit", "pwm"], 26: ["analog", "digit"]}

    def test_update_does_not_create_pins_again(self, channels, category, device_status):
        """Saving an existing device does not run the datasheet again: a deleted pin is not recreated."""
        # GIVEN
        device = Device.objects.create(name="Card", uid="AABBCCDDEEFF0011", category=category, status=device_status)
        Pin.objects.filter(device=device, pin_number=26).delete()

        # WHEN
        device.name = "Renamed card"
        device.save()

        # THEN
        assert sorted(available_channels_by_pin(device)) == [0]

    def test_creation_with_unknown_channel_creates_no_device(self, category, device_status):
        """A datasheet channel missing from the database cancels the creation: no device and no pin."""
        # GIVEN - no Channel in database

        # WHEN / THEN
        with pytest.raises(Channel.DoesNotExist):
            Device.objects.create(name="Card", uid="AABBCCDDEEFF0011", category=category, status=device_status)
        assert not Device.objects.exists()
        assert not Pin.objects.exists()

    def test_seeded_pico_gets_its_29_pins(self, device_status):
        """With the seeded channels and the seeded Raspberry Pi Pico, a new device gets its 29 pins."""
        # GIVEN
        ChannelSeeder(success_logger=lambda msg: None, error_logger=lambda msg: None).seed()
        DeviceCategorySeeder(success_logger=lambda msg: None, error_logger=lambda msg: None).seed()
        pico = DeviceCategory.objects.get(seed_id=1)

        # WHEN
        device = Device.objects.create(name="Pico", uid="AABBCCDDEEFF0011", category=pico, status=device_status)

        # THEN
        channels_by_pin = available_channels_by_pin(device)
        assert sorted(channels_by_pin) == list(range(29))
        assert channels_by_pin[0] == ["digit", "pwm"]
        assert [number for number, names in channels_by_pin.items() if "analog" in names] == [26, 27, 28]
        assert channels_by_pin[26] == ["analog", "digit", "pwm"]
