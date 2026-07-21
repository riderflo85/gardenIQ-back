import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.serializers import ControllerCategoryReadOnlySerializer
from gardeniq.hardware.serializers import ControllerCategorySerializer
from gardeniq.hardware.serializers import ControllerDetailReadOnlySerializer
from gardeniq.hardware.serializers import ControllerListReadOnlySerializer
from gardeniq.hardware.serializers import ControllerSerializer

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_serial_ports(mocker):
    """Mock serial port discovery to avoid hardware dependency in tests."""
    mock = mocker.patch("gardeniq.hardware.serializers.device.get_serial_port_choices")
    mock.return_value = ["/dev/ttyUSB0", "/dev/ttyUSB1"]
    return mock


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
    return Channel.objects.create(name="Digital")


@pytest.fixture
def pin(device, channel):
    p = Pin.objects.create(
        device=device,
        channel_choiced=channel,
        pin_number=1,
    )
    p.channels_available.set([channel])
    return p


@pytest.fixture
def controller_category(db):
    return ControllerCategory.objects.create(name="Relay")


@pytest.fixture
def controller(controller_category, device, pin):
    return Controller.objects.create(
        name="Main Relay",
        category=controller_category,
        device=device,
        pin=pin,
    )


# ─── ControllerCategorySerializer ─────────────────────────────────────────────


@pytest.mark.django_db
class TestControllerCategorySerializer:
    """Tests for ControllerCategorySerializer (writable)."""

    def test_valid_serializer(self):
        """
        GIVEN: valid data for a ControllerCategory
        WHEN: validating through ControllerCategorySerializer
        THEN: the serializer is valid and data matches the input
        """
        # GIVEN
        data = {"name": "Relay", "pin_init_cfg": {"mode": "output"}}
        expected = {"name": "Relay", "pin_init_cfg": {"mode": "output"}}

        # WHEN
        serializer = ControllerCategorySerializer(data=data)

        # THEN
        assert serializer.is_valid()
        assert serializer.data == expected

    def test_create(self):
        """
        GIVEN: valid data for a ControllerCategory
        WHEN: saving the serializer
        THEN: a ControllerCategory is created with the correct values
        """
        # GIVEN
        data = {"name": "Motor Controller", "pin_init_cfg": {}}

        # WHEN
        serializer = ControllerCategorySerializer(data=data)
        assert serializer.is_valid()
        category = serializer.save()

        # THEN
        assert isinstance(category, ControllerCategory)
        assert ControllerCategory.objects.count() == 1
        assert category.name == data["name"]
        assert category.pin_init_cfg == data["pin_init_cfg"]

    def test_create_with_nested_pin_init_cfg(self):
        """
        GIVEN: valid data with a nested pin_init_cfg
        WHEN: saving the serializer
        THEN: the ControllerCategory stores the nested configuration correctly
        """
        # GIVEN
        cfg = {"mode": "output", "settings": {"pull": "none", "value": 0}}
        data = {"name": "LED Driver", "pin_init_cfg": cfg}

        # WHEN
        serializer = ControllerCategorySerializer(data=data)
        assert serializer.is_valid()
        category = serializer.save()

        # THEN
        assert category.pin_init_cfg == cfg

    def test_update(self, controller_category):
        """
        GIVEN: an existing ControllerCategory and new data
        WHEN: updating through ControllerCategorySerializer
        THEN: the category is updated with the new values
        """
        # GIVEN
        updated_data = {"name": "Updated Relay", "pin_init_cfg": {"mode": "input"}}

        # WHEN
        serializer = ControllerCategorySerializer(instance=controller_category, data=updated_data)
        assert serializer.is_valid()
        category = serializer.save()

        # THEN
        assert isinstance(category, ControllerCategory)
        assert ControllerCategory.objects.count() == 1
        assert category.name == updated_data["name"]
        assert category.pin_init_cfg == updated_data["pin_init_cfg"]

    def test_serialized_instance(self, controller_category):
        """
        GIVEN: an existing ControllerCategory instance
        WHEN: serializing with ControllerCategorySerializer
        THEN: the serializer data contains all expected fields with correct values
        """
        # GIVEN
        expected = {
            "id": controller_category.pk,
            "name": controller_category.name,
            "pin_init_cfg": controller_category.pin_init_cfg,
        }

        # WHEN
        serializer = ControllerCategorySerializer(instance=controller_category)

        # THEN
        assert serializer.data == expected


# ─── ControllerCategoryReadOnlySerializer ─────────────────────────────────────


@pytest.mark.django_db
class TestControllerCategoryReadOnlySerializer:
    """Tests for ControllerCategoryReadOnlySerializer (read-only)."""

    def test_cannot_save(self):
        """
        GIVEN: valid data for a ControllerCategory
        WHEN: attempting to save a read-only serializer
        THEN: a NotImplementedError is raised and nothing is created
        """
        # GIVEN
        count_before = ControllerCategory.objects.count()
        data = {"name": "Relay", "pin_init_cfg": {}}

        # WHEN
        serializer = ControllerCategoryReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        assert ControllerCategory.objects.count() == count_before

    def test_cannot_update(self, controller_category):
        """
        GIVEN: an existing ControllerCategory and updated data
        WHEN: attempting to save a read-only serializer with an instance
        THEN: a NotImplementedError is raised and the category is not modified
        """
        # GIVEN
        original_name = controller_category.name
        data = {"name": "Updated Relay", "pin_init_cfg": {}}

        # WHEN
        serializer = ControllerCategoryReadOnlySerializer(instance=controller_category, data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        refreshed = ControllerCategory.objects.get(pk=controller_category.pk)
        assert refreshed.name == original_name

    def test_serialized_instance(self, controller_category):
        """
        GIVEN: an existing ControllerCategory instance
        WHEN: serializing with ControllerCategoryReadOnlySerializer
        THEN: the serializer data matches the expected representation
        """
        # GIVEN
        expected = {
            "id": controller_category.pk,
            "name": controller_category.name,
            "pin_init_cfg": controller_category.pin_init_cfg,
        }

        # WHEN
        serializer = ControllerCategoryReadOnlySerializer(instance=controller_category)

        # THEN
        assert serializer.data == expected


# ─── ControllerSerializer ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestControllerSerializer:
    """Tests for ControllerSerializer (writable)."""

    def test_valid_serializer(self, controller_category, device, pin):
        """
        GIVEN: valid data using PKs for all related objects
        WHEN: validating through ControllerSerializer
        THEN: the serializer is valid and data contains the correct PKs
        """
        # GIVEN
        data = {
            "name": "Main Relay",
            "category": controller_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }
        expected = {
            "name": "Main Relay",
            "category": controller_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = ControllerSerializer(data=data)

        # THEN
        assert serializer.is_valid()
        assert serializer.data == expected

    def test_create(self, controller_category, device, pin):
        """
        GIVEN: valid data for a Controller
        WHEN: saving the serializer
        THEN: a Controller is created with the correct name and linked objects
        """
        # GIVEN
        data = {
            "name": "Main Relay",
            "category": controller_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = ControllerSerializer(data=data)
        assert serializer.is_valid()
        ctrl = serializer.save()

        # THEN
        assert isinstance(ctrl, Controller)
        assert Controller.objects.count() == 1
        assert ctrl.name == data["name"]
        assert ctrl.category == controller_category
        assert ctrl.device == device
        assert ctrl.pin == pin

    def test_update(self, controller, device, channel):
        """
        GIVEN: an existing Controller and updated data with new related objects
        WHEN: updating through ControllerSerializer
        THEN: the Controller is updated with the new values
        """
        # GIVEN
        new_category = ControllerCategory.objects.create(name="Motor Controller")
        new_pin = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        updated_data = {
            "name": "Updated Relay",
            "category": new_category.pk,
            "device": device.pk,
            "pin": new_pin.pk,
        }

        # WHEN
        serializer = ControllerSerializer(instance=controller, data=updated_data)
        assert serializer.is_valid()
        ctrl = serializer.save()

        # THEN
        assert isinstance(ctrl, Controller)
        assert Controller.objects.count() == 1
        assert ctrl.name == updated_data["name"]
        assert ctrl.category == new_category
        assert ctrl.pin == new_pin

    def test_serialized_instance(self, controller, controller_category, device, pin):
        """
        GIVEN: an existing Controller instance
        WHEN: serializing with ControllerSerializer
        THEN: the serializer data contains the PKs of all related objects
        """
        # GIVEN
        expected = {
            "id": controller.pk,
            "name": controller.name,
            "category": controller_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = ControllerSerializer(instance=controller)

        # THEN
        assert serializer.data == expected


# ─── ControllerListReadOnlySerializer ─────────────────────────────────────────


@pytest.mark.django_db
class TestControllerListReadOnlySerializer:
    """Tests for ControllerListReadOnlySerializer (read-only with nested objects)."""

    def test_cannot_save(self, controller_category, device, pin):
        """
        GIVEN: valid data for a Controller
        WHEN: attempting to save a read-only serializer
        THEN: a NotImplementedError is raised and nothing is created
        """
        # GIVEN
        count_before = Controller.objects.count()
        data = {
            "name": "Main Relay",
            "category": controller_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = ControllerListReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        assert Controller.objects.count() == count_before

    def test_cannot_update(self, controller, controller_category, device, pin):
        """
        GIVEN: an existing Controller and updated data
        WHEN: attempting to save a read-only serializer with an instance
        THEN: a NotImplementedError is raised and the Controller is not modified
        """
        # GIVEN
        original_name = controller.name
        data = {
            "name": "Updated Relay",
            "category": controller_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = ControllerListReadOnlySerializer(instance=controller, data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        refreshed = Controller.objects.get(pk=controller.pk)
        assert refreshed.name == original_name

    def test_serialized_instance(self, controller, controller_category, device, pin, channel, device_status):
        """
        GIVEN: an existing Controller instance with all related objects
        WHEN: serializing with ControllerListReadOnlySerializer
        THEN: the related objects are represented in their minimal nested form
        """
        # GIVEN
        expected = {
            "id": controller.pk,
            "name": controller.name,
            "category": {
                "id": controller_category.pk,
                "name": controller_category.name,
            },
            "device": {
                "id": device.pk,
                "name": device.name,
                "status": {
                    "id": device_status.pk,
                    "name": device_status.name,
                    "description": device_status.description,
                    "tag": device_status.tag,
                    "color": device_status.color,
                },
            },
            "pin": {
                "id": pin.pk,
                "pin_number": pin.pin_number,
                "channel_choiced": channel.name,
            },
        }

        # WHEN
        serializer = ControllerListReadOnlySerializer(instance=controller)

        # THEN
        assert serializer.data == expected

    def test_serialized_multiple_instances(self, controller, controller_category, device, channel):
        """
        GIVEN: multiple existing Controller instances
        WHEN: serializing with ControllerListReadOnlySerializer using many=True
        THEN: all instances appear in the serialized list with correct names
        """
        # GIVEN
        second_pin = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        second_pin.channels_available.set([channel])
        second_ctrl = Controller.objects.create(
            name="Second Relay",
            category=controller_category,
            device=device,
            pin=second_pin,
        )
        queryset = Controller.objects.order_by("pk")

        # WHEN
        serializer = ControllerListReadOnlySerializer(instance=queryset, many=True)

        # THEN
        assert len(serializer.data) == 2
        names = [item["name"] for item in serializer.data]
        assert controller.name in names
        assert second_ctrl.name in names


# ─── ControllerDetailReadOnlySerializer ───────────────────────────────────────


@pytest.mark.django_db
class TestControllerDetailReadOnlySerializer:
    """Tests for ControllerDetailReadOnlySerializer (read-only with full device details)."""

    def test_cannot_save(self, controller_category, device, pin):
        """
        GIVEN: valid data for a Controller
        WHEN: attempting to save a read-only serializer
        THEN: a NotImplementedError is raised and nothing is created
        """
        # GIVEN
        count_before = Controller.objects.count()
        data = {
            "name": "Main Relay",
            "category": controller_category.pk,
            "device": device.pk,
            "pin": pin.pk,
        }

        # WHEN
        serializer = ControllerDetailReadOnlySerializer(data=data)
        assert serializer.is_valid()
        with pytest.raises(NotImplementedError):
            serializer.save()

        # THEN
        assert Controller.objects.count() == count_before

    def test_serialized_instance_controller_and_category_fields(self, controller, controller_category, pin, channel):
        """
        GIVEN: an existing Controller instance
        WHEN: serializing with ControllerDetailReadOnlySerializer
        THEN: id, name, category and pin fields are correctly represented
        """
        # GIVEN
        serializer = ControllerDetailReadOnlySerializer(instance=controller)

        # WHEN
        data = serializer.data

        # THEN
        assert data["id"] == controller.pk
        assert data["name"] == controller.name
        assert data["category"] == {
            "id": controller_category.pk,
            "name": controller_category.name,
        }
        assert data["pin"] == {
            "id": pin.pk,
            "pin_number": pin.pin_number,
            "channel_choiced": channel.name,
        }

    def test_serialized_instance_device_detail_fields(self, controller, device, device_status):
        """
        GIVEN: an existing Controller instance with a Device
        WHEN: serializing with ControllerDetailReadOnlySerializer
        THEN: the nested device contains full detail fields including uid, firmware versions and status
        """
        # GIVEN
        serializer = ControllerDetailReadOnlySerializer(instance=controller)

        # WHEN
        device_data = dict(serializer.data["device"])

        # THEN - last_seen is auto_now and dynamic, check separately
        last_seen = device_data.pop("last_seen")
        assert isinstance(last_seen, str)
        assert device_data == {
            "id": device.pk,
            "name": device.name,
            "description": device.description,
            "uid": device.uid,
            "path": device.path,
            "gd_firmware_version": device.gd_firmware_version,
            "mp_firmware_version": device.mp_firmware_version,
            "need_upgrade": device.need_upgrade,
            "status": {
                "id": device_status.pk,
                "name": device_status.name,
                "description": device_status.description,
                "tag": device_status.tag,
                "color": device_status.color,
            },
        }
