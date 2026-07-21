from rest_framework import status

import pytest

from gardeniq.base.models import Status
from gardeniq.base.utils.tests import ViewSetTestMixin
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin

# ─── Channel View Tests ────────────────────────────────────────────────────────


@pytest.mark.django_db
class ChannelViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "channels"
    MODEL = Channel
    DATA_TO_DEFAULT_OBJ = {"name": "Analog"}

    def generate_default_obj(self):
        ch1 = Channel.objects.create(name="Analog", description="Analog input/output channel")
        ch2 = Channel.objects.create(name="Digital")
        return ch1, ch2


@pytest.mark.django_db
class TestChannelAPIModelView(ChannelViewSetTestConf):

    def test_list(self, authenticated_client, obj):
        """
        GIVEN: two existing Channel instances
        WHEN: performing a GET request on the channels list endpoint
        THEN: the response returns 200 with both channels and the expected fields
        """
        # GIVEN
        ch1, ch2 = obj
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        names = [item["name"] for item in response.data["results"]]
        assert ch1.name in names
        assert ch2.name in names
        first = response.data["results"][0]
        assert "id" in first
        assert "name" in first
        assert "description" in first

    def test_retrieve(self, authenticated_client, obj):
        """
        GIVEN: an existing Channel
        WHEN: performing a GET request on its detail endpoint
        THEN: the response returns 200 with the correct id, name and description
        """
        # GIVEN
        ch1, _ = obj
        url = self.get_url_detail(ch1)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == ch1.pk
        assert response.data["name"] == ch1.name
        assert response.data["description"] == ch1.description

    def test_post_not_allowed(self, authenticated_client):
        """
        GIVEN: the channels endpoint
        WHEN: performing a POST request
        THEN: the response returns 405 Method Not Allowed
        """
        # GIVEN
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, {"name": "New Channel"}, format="json")

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_not_allowed(self, authenticated_client, obj):
        """
        GIVEN: an existing Channel
        WHEN: performing a PUT request on its detail endpoint
        THEN: the response returns 405 Method Not Allowed
        """
        # GIVEN
        ch1, _ = obj
        url = self.get_url_detail(ch1)

        # WHEN
        response = authenticated_client.put(url, {"name": "Updated"}, format="json")

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, authenticated_client, obj):
        """
        GIVEN: an existing Channel
        WHEN: performing a DELETE request on its detail endpoint
        THEN: the response returns 405 Method Not Allowed
        """
        # GIVEN
        ch1, _ = obj
        url = self.get_url_detail(ch1)

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_not_allowed(self, authenticated_client, obj):
        """
        GIVEN: an existing Channel
        WHEN: performing a PATCH request on its detail endpoint
        THEN: the response returns 405 Method Not Allowed
        """
        # GIVEN
        ch1, _ = obj
        url = self.get_url_detail(ch1)

        # WHEN
        response = authenticated_client.patch(url, {"name": "Partial"})

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ─── Pin View Tests ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class PinViewSetTestConf(ViewSetTestMixin):
    BASE_PATTERN = "pins"
    MODEL = Pin
    DATA_TO_DEFAULT_OBJ = {}

    @pytest.fixture
    def device_status(self, db):
        return Status.objects.create(name="Generic", tag="device-generic", color="#123456")

    @pytest.fixture
    def device(self, device_status):
        return Device.objects.create(
            name="Test Device",
            uid="AABBCCDDEEFF0011",
            path="/dev/ttyUSB0",
            status=device_status,
        )

    @pytest.fixture
    def channel(self, db):
        return Channel.objects.create(name="Analog")

    @pytest.fixture
    def obj(self, device, channel):
        pin1 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=1)
        pin1.channels_available.set([channel])
        pin2 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        pin2.channels_available.set([channel])
        return pin1, pin2


@pytest.mark.django_db
class TestPinAPIModelView(PinViewSetTestConf):

    def test_list(self, authenticated_client, obj):
        """
        GIVEN: two existing Pin instances
        WHEN: performing a GET request on the pins list endpoint
        THEN: the response returns 200 with both pins in minimal representation (id, pin_number, channel name)
        """
        # GIVEN
        pin1, pin2 = obj
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        pin_numbers = [item["pin_number"] for item in response.data["results"]]
        assert pin1.pin_number in pin_numbers
        assert pin2.pin_number in pin_numbers
        first = response.data["results"][0]
        assert "id" in first
        assert "pin_number" in first
        assert "channel_choiced" in first
        assert isinstance(first["channel_choiced"], str)

    def test_retrieve_scalar_fields(self, authenticated_client, obj):
        """
        GIVEN: an existing Pin
        WHEN: performing a GET request on its detail endpoint
        THEN: the response returns 200 with id and pin_number correct
        """
        # GIVEN
        pin1, _ = obj
        url = self.get_url_detail(pin1)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == pin1.pk
        assert response.data["pin_number"] == pin1.pin_number

    def test_retrieve_channel_choiced_is_nested(self, authenticated_client, obj, channel):
        """
        GIVEN: an existing Pin linked to a Channel
        WHEN: performing a GET request on the pin detail endpoint
        THEN: channel_choiced is represented as a nested object with id, name and description
        """
        # GIVEN
        pin1, _ = obj
        url = self.get_url_detail(pin1)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        channel_choiced = response.data["channel_choiced"]
        assert isinstance(channel_choiced, dict)
        assert channel_choiced["id"] == channel.pk
        assert channel_choiced["name"] == channel.name
        assert "description" in channel_choiced

    def test_retrieve_channels_available_is_list(self, authenticated_client, obj, channel):
        """
        GIVEN: an existing Pin with one channel in channels_available
        WHEN: performing a GET request on the pin detail endpoint
        THEN: channels_available is a list of nested channel objects
        """
        # GIVEN
        pin1, _ = obj
        url = self.get_url_detail(pin1)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        channels_available = response.data["channels_available"]
        assert isinstance(channels_available, list)
        assert len(channels_available) == 1
        assert channels_available[0]["id"] == channel.pk
        assert channels_available[0]["name"] == channel.name

    def test_retrieve_device_is_nested(self, authenticated_client, obj, device, device_status):
        """
        GIVEN: an existing Pin linked to a Device
        WHEN: performing a GET request on the pin detail endpoint
        THEN: device is represented as a nested object with id, name and a nested status
        """
        # GIVEN
        pin1, _ = obj
        url = self.get_url_detail(pin1)

        # WHEN
        response = authenticated_client.get(url)

        # THEN
        device_data = response.data["device"]
        assert isinstance(device_data, dict)
        assert device_data["id"] == device.pk
        assert device_data["name"] == device.name
        assert isinstance(device_data["status"], dict)
        assert device_data["status"]["id"] == device_status.pk
        assert device_data["status"]["tag"] == device_status.tag

    def test_post_not_allowed(self, authenticated_client):
        """
        GIVEN: the pins endpoint
        WHEN: performing a POST request
        THEN: the response returns 405 Method Not Allowed
        """
        # GIVEN
        url = self.get_url_list()

        # WHEN
        response = authenticated_client.post(url, {}, format="json")

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_put_not_allowed(self, authenticated_client, obj):
        """
        GIVEN: an existing Pin
        WHEN: performing a PUT request on its detail endpoint
        THEN: the response returns 405 Method Not Allowed
        """
        # GIVEN
        pin1, _ = obj
        url = self.get_url_detail(pin1)

        # WHEN
        response = authenticated_client.put(url, {}, format="json")

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, authenticated_client, obj):
        """
        GIVEN: an existing Pin
        WHEN: performing a DELETE request on its detail endpoint
        THEN: the response returns 405 Method Not Allowed
        """
        # GIVEN
        pin1, _ = obj
        url = self.get_url_detail(pin1)

        # WHEN
        response = authenticated_client.delete(url)

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_patch_not_allowed(self, authenticated_client, obj):
        """
        GIVEN: an existing Pin
        WHEN: performing a PATCH request on its detail endpoint
        THEN: the response returns 405 Method Not Allowed
        """
        # GIVEN
        pin1, _ = obj
        url = self.get_url_detail(pin1)

        # WHEN
        response = authenticated_client.patch(url, {"pin_number": 99})

        # THEN
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
