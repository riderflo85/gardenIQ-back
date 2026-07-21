from django.db import IntegrityError
from django.db.models import ProtectedError

import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def device_status(db):
    return Status.objects.create(name="Generic", tag="device-generic", color="#123456")


@pytest.fixture
def device(device_status):
    return Device.objects.create(
        name="Test Device",
        uid="AABBCCDDEEFF0011",
        path="/dev/ttyUSB0",
        status=device_status,
    )


@pytest.fixture
def channel(db):
    return Channel.objects.create(name="Analog")


@pytest.fixture
def pin(device, channel):
    p = Pin.objects.create(
        device=device,
        channel_choiced=channel,
        pin_number=1,
    )
    p.channels_available.set([channel])
    return p


# ─── Channel Tests ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestChannelCreation:
    """Tests for Channel model creation."""

    def test_create_with_name_only(self):
        """
        GIVEN: a name for a Channel
        WHEN: creating a Channel without specifying description
        THEN: the Channel is created with an empty description
        """
        # GIVEN / WHEN
        channel = Channel.objects.create(name="Digital")

        # THEN
        assert channel.pk is not None
        assert channel.name == "Digital"
        assert channel.description == ""

    def test_create_with_description(self):
        """
        GIVEN: a name and a description for a Channel
        WHEN: creating a Channel with both fields
        THEN: the Channel is created with the correct values
        """
        # GIVEN / WHEN
        channel = Channel.objects.create(name="PWM", description="Pulse-width modulation channel")

        # THEN
        assert channel.pk is not None
        assert channel.description == "Pulse-width modulation channel"

    def test_create_multiple_channels(self):
        """
        GIVEN: data for multiple Channels
        WHEN: creating multiple Channels
        THEN: all Channels are persisted in the database
        """
        # GIVEN
        names = ["Analog", "Digital", "PWM", "I2C"]

        # WHEN
        for name in names:
            Channel.objects.create(name=name)

        # THEN
        assert Channel.objects.count() == len(names)


@pytest.mark.django_db
class TestChannelDescription:
    """Tests for Channel description field."""

    def test_description_defaults_to_empty_string(self):
        """
        GIVEN: no description provided
        WHEN: creating a Channel without specifying description
        THEN: the field defaults to an empty string
        """
        # GIVEN / WHEN
        channel = Channel.objects.create(name="SPI")

        # THEN
        assert channel.description == ""

    def test_description_can_be_updated(self, channel):
        """
        GIVEN: an existing Channel with no description
        WHEN: updating the description
        THEN: the new value is persisted correctly
        """
        # GIVEN
        new_description = "Analog input channel"

        # WHEN
        channel.description = new_description
        channel.save()

        # THEN
        refreshed = Channel.objects.get(pk=channel.pk)
        assert refreshed.description == new_description

    def test_name_can_be_updated(self, channel):
        """
        GIVEN: an existing Channel
        WHEN: updating its name
        THEN: the new name is persisted correctly
        """
        # GIVEN
        new_name = "Digital"

        # WHEN
        channel.name = new_name
        channel.save()

        # THEN
        refreshed = Channel.objects.get(pk=channel.pk)
        assert refreshed.name == new_name


@pytest.mark.django_db
class TestChannelRelations:
    """Tests for Channel reverse relations."""

    def test_choiced_pins_reverse_relation_returns_linked_pin(self, pin, channel):
        """
        GIVEN: a Pin with channel_choiced set to a Channel
        WHEN: accessing the choiced_pins reverse relation on the Channel
        THEN: the related Pin is returned
        """
        # GIVEN - fixture creates a Pin linked to the channel

        # WHEN
        related = channel.choiced_pins.all()

        # THEN
        assert related.count() == 1
        assert pin in related

    def test_available_pins_reverse_relation_returns_linked_pin(self, pin, channel):
        """
        GIVEN: a Pin with channels_available containing a Channel
        WHEN: accessing the available_pins reverse relation on the Channel
        THEN: the related Pin is returned
        """
        # GIVEN - fixture creates a Pin with channels_available set to the channel

        # WHEN
        related = channel.available_pins.all()

        # THEN
        assert related.count() == 1
        assert pin in related

    def test_choiced_pins_is_empty_when_no_pins(self, channel):
        """
        GIVEN: a Channel with no Pins referencing it as channel_choiced
        WHEN: accessing the choiced_pins reverse relation
        THEN: an empty queryset is returned
        """
        # GIVEN - no Pin is created

        # WHEN
        related = channel.choiced_pins.all()

        # THEN
        assert related.count() == 0


@pytest.mark.django_db
class TestChannelDeletion:
    """Tests for Channel deletion behavior."""

    def test_delete_channel_without_pins(self, channel):
        """
        GIVEN: a Channel not referenced by any Pin
        WHEN: deleting the Channel
        THEN: the Channel is removed from the database
        """
        # GIVEN
        channel_id = channel.pk

        # WHEN
        channel.delete()

        # THEN
        assert not Channel.objects.filter(pk=channel_id).exists()

    def test_delete_channel_raises_protected_error_when_used_as_channel_choiced(self, pin, channel):
        """
        GIVEN: a Channel used as channel_choiced of a Pin
        WHEN: attempting to delete the Channel
        THEN: a ProtectedError is raised and the Pin is preserved
        """
        # GIVEN - fixture creates a Pin with channel_choiced=channel

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            channel.delete()

        assert Pin.objects.filter(pk=pin.pk).exists()

    def test_delete_channel_used_only_in_channels_available_succeeds(self, device, channel):
        """
        GIVEN: a Channel referenced only in channels_available of a Pin (not as channel_choiced)
        WHEN: removing it from channels_available and deleting it
        THEN: the Channel is removed from the database
        """
        # GIVEN
        other_channel = Channel.objects.create(name="Digital")
        p = Pin.objects.create(device=device, channel_choiced=other_channel, pin_number=2)
        p.channels_available.set([channel])
        channel_id = channel.pk

        # WHEN
        p.channels_available.remove(channel)
        channel.delete()

        # THEN
        assert not Channel.objects.filter(pk=channel_id).exists()


# ─── Pin Tests ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPinCreation:
    """Tests for Pin model creation."""

    def test_create_pin_with_required_fields(self, device, channel):
        """
        GIVEN: a Device, a Channel and a pin_number
        WHEN: creating a Pin with all required fields
        THEN: the Pin is created with the correct values
        """
        # GIVEN / WHEN
        p = Pin.objects.create(device=device, channel_choiced=channel, pin_number=1)

        # THEN
        assert p.pk is not None
        assert p.device == device
        assert p.channel_choiced == channel
        assert p.pin_number == 1

    def test_create_pin_with_channels_available(self, device, channel):
        """
        GIVEN: a Device, a Channel and a list of available channels
        WHEN: creating a Pin and assigning channels_available
        THEN: the Pin is created and channels_available contains the expected Channel
        """
        # GIVEN
        extra_channel = Channel.objects.create(name="Digital")
        p = Pin.objects.create(device=device, channel_choiced=channel, pin_number=3)

        # WHEN
        p.channels_available.set([channel, extra_channel])

        # THEN
        assert p.channels_available.count() == 2
        assert channel in p.channels_available.all()
        assert extra_channel in p.channels_available.all()

    def test_create_multiple_pins_on_same_device(self, device, channel):
        """
        GIVEN: a Device and multiple distinct pin numbers
        WHEN: creating multiple Pins on the same Device
        THEN: all Pins are persisted in the database
        """
        # GIVEN / WHEN
        Pin.objects.create(device=device, channel_choiced=channel, pin_number=1)
        Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        Pin.objects.create(device=device, channel_choiced=channel, pin_number=3)

        # THEN
        assert Pin.objects.count() == 3


@pytest.mark.django_db
class TestPinConstraints:
    """Tests for Pin model constraints."""

    def test_unique_device_pin_number_constraint(self, pin, device, channel):
        """
        GIVEN: a Pin already existing with a given device and pin_number
        WHEN: creating another Pin with the same device and pin_number
        THEN: an IntegrityError is raised
        """
        # GIVEN - fixture creates Pin(device=device, pin_number=1)

        # WHEN / THEN
        with pytest.raises(IntegrityError):
            Pin.objects.create(device=device, channel_choiced=channel, pin_number=1)

    def test_same_pin_number_on_different_devices_is_allowed(self, device, channel, device_status):
        """
        GIVEN: two distinct Devices
        WHEN: creating a Pin with the same pin_number on each Device
        THEN: both Pins are created without error
        """
        # GIVEN
        other_device = Device.objects.create(
            name="Other Device",
            uid="1122334455667788",
            path="/dev/ttyUSB1",
            status=device_status,
        )

        # WHEN
        p1 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=1)
        p2 = Pin.objects.create(device=other_device, channel_choiced=channel, pin_number=1)

        # THEN
        assert p1.pk is not None
        assert p2.pk is not None


@pytest.mark.django_db
class TestPinRelations:
    """Tests for Pin foreign key and M2M relationships."""

    def test_device_relation_returns_correct_device(self, pin, device):
        """
        GIVEN: a Pin linked to a Device
        WHEN: accessing the device attribute
        THEN: the correct Device is returned
        """
        # GIVEN - fixture creates the Pin with the device

        # WHEN
        result = pin.device

        # THEN
        assert result == device

    def test_channel_choiced_relation_returns_correct_channel(self, pin, channel):
        """
        GIVEN: a Pin with a channel_choiced set
        WHEN: accessing the channel_choiced attribute
        THEN: the correct Channel is returned
        """
        # GIVEN - fixture creates the Pin with channel_choiced=channel

        # WHEN
        result = pin.channel_choiced

        # THEN
        assert result == channel

    def test_channels_available_returns_assigned_channels(self, pin, channel):
        """
        GIVEN: a Pin with channels_available set
        WHEN: accessing the channels_available queryset
        THEN: the assigned Channel is present
        """
        # GIVEN - fixture creates the Pin with channels_available=[channel]

        # WHEN
        result = pin.channels_available.all()

        # THEN
        assert channel in result

    def test_device_reverse_relation_includes_pin(self, pin, device):
        """
        GIVEN: a Pin linked to a Device
        WHEN: accessing the pins reverse relation on the Device
        THEN: the related Pin is returned
        """
        # GIVEN - fixture creates the Pin linked to the device

        # WHEN
        related = device.pins.all()

        # THEN
        assert related.count() == 1
        assert pin in related


@pytest.mark.django_db
class TestPinUpdate:
    """Tests for Pin model update operations."""

    def test_update_pin_number(self, pin):
        """
        GIVEN: an existing Pin
        WHEN: updating its pin_number
        THEN: the new value is persisted correctly
        """
        # GIVEN
        new_number = 42

        # WHEN
        pin.pin_number = new_number
        pin.save()

        # THEN
        updated = Pin.objects.get(pk=pin.pk)
        assert updated.pin_number == new_number

    def test_update_channel_choiced(self, pin, device):
        """
        GIVEN: an existing Pin and a new Channel
        WHEN: assigning the new Channel as channel_choiced
        THEN: the FK is updated correctly in the database
        """
        # GIVEN
        new_channel = Channel.objects.create(name="Digital")

        # WHEN
        pin.channel_choiced = new_channel
        pin.save()

        # THEN
        updated = Pin.objects.get(pk=pin.pk)
        assert updated.channel_choiced == new_channel

    def test_update_channels_available(self, pin):
        """
        GIVEN: an existing Pin with one Channel in channels_available
        WHEN: replacing channels_available with a new set of Channels
        THEN: channels_available reflects the new set
        """
        # GIVEN
        new_channel = Channel.objects.create(name="I2C")

        # WHEN
        pin.channels_available.set([new_channel])

        # THEN
        updated = Pin.objects.get(pk=pin.pk)
        available = updated.channels_available.all()
        assert available.count() == 1
        assert new_channel in available


@pytest.mark.django_db
class TestPinDeletion:
    """Tests for Pin model deletion behavior."""

    def test_delete_pin(self, pin):
        """
        GIVEN: an existing Pin
        WHEN: deleting the Pin
        THEN: the Pin no longer exists in the database
        """
        # GIVEN
        pin_id = pin.pk

        # WHEN
        pin.delete()

        # THEN
        assert not Pin.objects.filter(pk=pin_id).exists()

    def test_delete_pin_does_not_delete_device(self, pin, device):
        """
        GIVEN: an existing Pin linked to a Device
        WHEN: deleting the Pin
        THEN: the Device is not deleted
        """
        # GIVEN
        device_id = device.pk

        # WHEN
        pin.delete()

        # THEN
        assert Device.objects.filter(pk=device_id).exists()

    def test_delete_pin_does_not_delete_channel(self, pin, channel):
        """
        GIVEN: an existing Pin linked to a Channel
        WHEN: deleting the Pin
        THEN: the Channel is not deleted
        """
        # GIVEN
        channel_id = channel.pk

        # WHEN
        pin.delete()

        # THEN
        assert Channel.objects.filter(pk=channel_id).exists()

    def test_delete_device_cascades_to_pin(self, pin, device):
        """
        GIVEN: a Pin linked to a Device
        WHEN: deleting the Device
        THEN: the Pin is also deleted (CASCADE)
        """
        # GIVEN
        pin_id = pin.pk

        # WHEN
        device.delete()

        # THEN
        assert not Pin.objects.filter(pk=pin_id).exists()

    def test_delete_channel_choiced_raises_protected_error(self, pin, channel):
        """
        GIVEN: a Pin whose channel_choiced points to a Channel
        WHEN: attempting to delete that Channel
        THEN: a ProtectedError is raised and the Pin is preserved
        """
        # GIVEN - fixture creates a Pin with channel_choiced=channel

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            channel.delete()

        assert Pin.objects.filter(pk=pin.pk).exists()
