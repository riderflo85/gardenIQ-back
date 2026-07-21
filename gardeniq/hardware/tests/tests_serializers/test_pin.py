import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.serializers import ChannelReadOnlySerializer
from gardeniq.hardware.serializers import ChannelSerializer
from gardeniq.hardware.serializers import PinDetailReadOnlySerializer
from gardeniq.hardware.serializers import PinMinimalReadOnlySerializer
from gardeniq.hardware.serializers import PinSerializer

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


# ─── ChannelSerializer ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestChannelSerializer:
    """Tests for ChannelSerializer (writable)."""

    def test_valid_data(self):
        """
        GIVEN: a name for a Channel
        WHEN: validating through ChannelSerializer without description
        THEN: the serializer is valid
        """
        # GIVEN
        data = {"name": "Analog"}

        # WHEN
        serializer = ChannelSerializer(data=data)

        # THEN
        assert serializer.is_valid()

    def test_valid_data_with_description(self):
        """
        GIVEN: a name and a description for a Channel
        WHEN: validating through ChannelSerializer
        THEN: the serializer is valid and data matches the input
        """
        # GIVEN
        data = {"name": "PWM", "description": "Pulse-width modulation channel"}

        # WHEN
        serializer = ChannelSerializer(data=data)

        # THEN
        assert serializer.is_valid()
        assert serializer.data["description"] == data["description"]

    def test_name_is_required(self):
        """
        GIVEN: data without the name field
        WHEN: validating through ChannelSerializer
        THEN: the serializer is invalid with an error on the name field
        """
        # GIVEN
        data = {"description": "Missing name"}

        # WHEN
        serializer = ChannelSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_create(self):
        """
        GIVEN: valid data for a Channel
        WHEN: saving the serializer
        THEN: a Channel is created with the correct values
        """
        # GIVEN
        data = {"name": "Digital"}

        # WHEN
        serializer = ChannelSerializer(data=data)
        assert serializer.is_valid()
        channel = serializer.save()

        # THEN
        assert isinstance(channel, Channel)
        assert Channel.objects.count() == 1
        assert channel.name == data["name"]
        assert channel.description == ""

    def test_create_with_description(self):
        """
        GIVEN: valid data including a description
        WHEN: saving the serializer
        THEN: a Channel is created with the correct name and description
        """
        # GIVEN
        data = {"name": "I2C", "description": "Inter-Integrated Circuit channel"}

        # WHEN
        serializer = ChannelSerializer(data=data)
        assert serializer.is_valid()
        channel = serializer.save()

        # THEN
        assert channel.description == data["description"]

    def test_update(self, channel):
        """
        GIVEN: an existing Channel and new data
        WHEN: updating through ChannelSerializer
        THEN: the Channel is updated with the new values
        """
        # GIVEN
        updated_data = {"name": "Digital", "description": "Updated description"}

        # WHEN
        serializer = ChannelSerializer(instance=channel, data=updated_data)
        assert serializer.is_valid()
        updated = serializer.save()

        # THEN
        assert updated.name == updated_data["name"]
        assert updated.description == updated_data["description"]
        assert Channel.objects.count() == 1

    def test_serialized_instance(self, channel):
        """
        GIVEN: an existing Channel instance
        WHEN: serializing with ChannelSerializer
        THEN: the serializer data contains all expected fields with correct values
        """
        # GIVEN
        expected = {
            "id": channel.pk,
            "name": channel.name,
            "description": channel.description,
        }

        # WHEN
        serializer = ChannelSerializer(instance=channel)

        # THEN
        assert serializer.data == expected


# ─── ChannelReadOnlySerializer ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestChannelReadOnlySerializer:
    """Tests for ChannelReadOnlySerializer (read-only)."""

    def test_cannot_save(self):
        """
        GIVEN: valid data for a Channel
        WHEN: attempting to save a read-only serializer
        THEN: a NotImplementedError is raised and nothing is created
        """
        # GIVEN
        count_before = Channel.objects.count()
        data = {"name": "Digital"}

        # WHEN
        serializer = ChannelReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        assert Channel.objects.count() == count_before

    def test_cannot_update(self, channel):
        """
        GIVEN: an existing Channel and updated data
        WHEN: attempting to save a read-only serializer with an instance
        THEN: a NotImplementedError is raised and the Channel is not modified
        """
        # GIVEN
        original_name = channel.name
        data = {"name": "Digital"}

        # WHEN
        serializer = ChannelReadOnlySerializer(instance=channel, data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        refreshed = Channel.objects.get(pk=channel.pk)
        assert refreshed.name == original_name

    def test_serialized_instance(self, channel):
        """
        GIVEN: an existing Channel instance
        WHEN: serializing with ChannelReadOnlySerializer
        THEN: the serializer data matches the expected representation
        """
        # GIVEN
        expected = {
            "id": channel.pk,
            "name": channel.name,
            "description": channel.description,
        }

        # WHEN
        serializer = ChannelReadOnlySerializer(instance=channel)

        # THEN
        assert serializer.data == expected


# ─── PinSerializer ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPinSerializer:
    """Tests for PinSerializer (writable)."""

    def test_valid_data(self, device, channel):
        """
        GIVEN: valid PKs for device, channel_choiced, channels_available and a pin_number
        WHEN: validating through PinSerializer
        THEN: the serializer is valid
        """
        # GIVEN
        data = {
            "device": device.pk,
            "channel_choiced": channel.pk,
            "channels_available": [channel.pk],
            "pin_number": 1,
        }

        # WHEN
        serializer = PinSerializer(data=data)

        # THEN
        assert serializer.is_valid(), serializer.errors

    def test_device_is_required(self, channel):
        """
        GIVEN: data missing the device field
        WHEN: validating through PinSerializer
        THEN: the serializer is invalid with an error on the device field
        """
        # GIVEN
        data = {
            "channel_choiced": channel.pk,
            "channels_available": [channel.pk],
            "pin_number": 1,
        }

        # WHEN
        serializer = PinSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "device" in serializer.errors

    def test_pin_number_is_required(self, device, channel):
        """
        GIVEN: data missing the pin_number field
        WHEN: validating through PinSerializer
        THEN: the serializer is invalid with an error on the pin_number field
        """
        # GIVEN
        data = {
            "device": device.pk,
            "channel_choiced": channel.pk,
            "channels_available": [channel.pk],
        }

        # WHEN
        serializer = PinSerializer(data=data)

        # THEN
        assert not serializer.is_valid()
        assert "pin_number" in serializer.errors

    def test_update(self, pin, device, channel):
        """
        GIVEN: an existing Pin and updated data with a new channel_choiced and pin_number
        WHEN: updating through PinSerializer
        THEN: the Pin is updated with the new values
        """
        # GIVEN
        new_channel = Channel.objects.create(name="Digital")
        updated_data = {
            "device": device.pk,
            "channel_choiced": new_channel.pk,
            "channels_available": [channel.pk],
            "pin_number": 5,
        }

        # WHEN
        serializer = PinSerializer(instance=pin, data=updated_data)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()

        # THEN
        assert updated.channel_choiced == new_channel
        assert updated.pin_number == 5

    def test_serialized_instance(self, pin, device, channel):
        """
        GIVEN: an existing Pin instance
        WHEN: serializing with PinSerializer
        THEN: the serializer data contains PKs for all related objects
        """
        # GIVEN
        expected = {
            "id": pin.pk,
            "device": device.pk,
            "channel_choiced": channel.pk,
            "channels_available": [channel.pk],
            "pin_number": pin.pin_number,
        }

        # WHEN
        serializer = PinSerializer(instance=pin)

        # THEN
        assert serializer.data == expected


# ─── PinDetailReadOnlySerializer ───────────────────────────────────────────────


@pytest.mark.django_db
class TestPinDetailReadOnlySerializer:
    """Tests for PinDetailReadOnlySerializer (read-only with nested objects)."""

    def test_cannot_save(self, device, channel):
        """
        GIVEN: valid data for a Pin
        WHEN: attempting to save a read-only serializer
        THEN: a NotImplementedError is raised and nothing is created
        """
        # GIVEN
        count_before = Pin.objects.count()
        data = {
            "device": device.pk,
            "channel_choiced": channel.pk,
            "channels_available": [channel.pk],
            "pin_number": 1,
        }

        # WHEN
        serializer = PinDetailReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        assert Pin.objects.count() == count_before

    def test_serialized_instance_channel_and_pin_fields(self, pin, channel, device_status, device):
        """
        GIVEN: an existing Pin instance
        WHEN: serializing with PinDetailReadOnlySerializer
        THEN: id, pin_number and channel_choiced are correctly represented in nested form
        """
        # GIVEN
        serializer = PinDetailReadOnlySerializer(instance=pin)

        # WHEN
        data = serializer.data

        # THEN
        assert data["id"] == pin.pk
        assert data["pin_number"] == pin.pin_number
        assert data["channel_choiced"] == {
            "id": channel.pk,
            "name": channel.name,
            "description": channel.description,
        }

    def test_serialized_instance_channels_available(self, pin, channel):
        """
        GIVEN: an existing Pin instance with one channel in channels_available
        WHEN: serializing with PinDetailReadOnlySerializer
        THEN: channels_available is a list of nested channel representations
        """
        # GIVEN
        serializer = PinDetailReadOnlySerializer(instance=pin)

        # WHEN
        channels_available = serializer.data["channels_available"]

        # THEN
        assert len(channels_available) == 1
        assert channels_available[0] == {
            "id": channel.pk,
            "name": channel.name,
            "description": channel.description,
        }

    def test_serialized_instance_device_field(self, pin, device, device_status):
        """
        GIVEN: an existing Pin instance with a Device
        WHEN: serializing with PinDetailReadOnlySerializer
        THEN: the nested device contains id, name and a nested status
        """
        # GIVEN
        serializer = PinDetailReadOnlySerializer(instance=pin)

        # WHEN
        device_data = serializer.data["device"]

        # THEN
        assert device_data == {
            "id": device.pk,
            "name": device.name,
            "status": {
                "id": device_status.pk,
                "name": device_status.name,
                "description": device_status.description,
                "tag": device_status.tag,
                "color": device_status.color,
            },
        }


# ─── PinMinimalReadOnlySerializer ──────────────────────────────────────────────


@pytest.mark.django_db
class TestPinMinimalReadOnlySerializer:
    """Tests for PinMinimalReadOnlySerializer (read-only minimal representation)."""

    def test_cannot_save(self, device, channel):
        """
        GIVEN: valid data for a Pin
        WHEN: attempting to save a read-only serializer
        THEN: a NotImplementedError is raised and nothing is created
        """
        # GIVEN
        count_before = Pin.objects.count()
        data = {
            "device": device.pk,
            "channel_choiced": channel.pk,
            "channels_available": [channel.pk],
            "pin_number": 1,
        }

        # WHEN
        serializer = PinMinimalReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        assert Pin.objects.count() == count_before

    def test_serialized_instance(self, pin, channel):
        """
        GIVEN: an existing Pin instance
        WHEN: serializing with PinMinimalReadOnlySerializer
        THEN: only id, pin_number and channel_choiced name are exposed
        """
        # GIVEN
        expected = {
            "id": pin.pk,
            "pin_number": pin.pin_number,
            "channel_choiced": channel.name,
        }

        # WHEN
        serializer = PinMinimalReadOnlySerializer(instance=pin)

        # THEN
        assert serializer.data == expected

    def test_serialized_multiple_instances(self, device, channel):
        """
        GIVEN: multiple existing Pin instances
        WHEN: serializing with PinMinimalReadOnlySerializer using many=True
        THEN: all instances appear in the list with their minimal fields
        """
        # GIVEN
        pin1 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=1)
        pin2 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        queryset = Pin.objects.order_by("pin_number")

        # WHEN
        serializer = PinMinimalReadOnlySerializer(instance=queryset, many=True)

        # THEN
        assert len(serializer.data) == 2
        pin_numbers = [item["pin_number"] for item in serializer.data]
        assert pin1.pin_number in pin_numbers
        assert pin2.pin_number in pin_numbers
