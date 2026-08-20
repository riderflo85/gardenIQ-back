from django.db.models import ProtectedError

import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
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


# ─── ControllerCategory Tests ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestControllerCategoryCreation:
    """Tests for ControllerCategory model creation."""

    def test_create_with_name_only(self):
        """
        GIVEN: a name for a ControllerCategory
        WHEN: creating a ControllerCategory without specifying pin_init_cfg
        THEN: the ControllerCategory is created with an empty dict as default pin_init_cfg
        """
        # GIVEN / WHEN
        category = ControllerCategory.objects.create(name="Relay")

        # THEN
        assert category.pk is not None
        assert category.name == "Relay"
        assert category.pin_init_cfg == {}

    def test_create_with_custom_pin_init_cfg(self):
        """
        GIVEN: a name and a custom pin_init_cfg dict
        WHEN: creating a ControllerCategory with this configuration
        THEN: the ControllerCategory is created with the provided configuration
        """
        # GIVEN
        cfg = {"mode": "output", "pull": "none"}

        # WHEN
        category = ControllerCategory.objects.create(name="LED Driver", pin_init_cfg=cfg)

        # THEN
        assert category.pk is not None
        assert category.pin_init_cfg == cfg

    def test_create_multiple_categories(self):
        """
        GIVEN: data for multiple ControllerCategories
        WHEN: creating multiple ControllerCategories
        THEN: all categories are persisted in the database
        """
        # GIVEN
        names = ["Relay", "LED Driver", "Motor Controller"]

        # WHEN
        for name in names:
            ControllerCategory.objects.create(name=name)

        # THEN
        assert ControllerCategory.objects.count() == len(names)


@pytest.mark.django_db
class TestControllerCategoryPinInitCfg:
    """Tests for ControllerCategory pin_init_cfg field."""

    def test_pin_init_cfg_defaults_to_empty_dict(self):
        """
        GIVEN: no pin_init_cfg value
        WHEN: creating a ControllerCategory without specifying pin_init_cfg
        THEN: the field defaults to an empty dict
        """
        # GIVEN / WHEN
        category = ControllerCategory.objects.create(name="Relay")

        # THEN
        assert category.pin_init_cfg == {}

    def test_pin_init_cfg_can_be_updated(self, controller_category):
        """
        GIVEN: an existing ControllerCategory with an empty pin_init_cfg
        WHEN: updating the pin_init_cfg with new values
        THEN: the new configuration is persisted correctly
        """
        # GIVEN
        new_cfg = {"frequency": 1000, "duty_cycle": 50}

        # WHEN
        controller_category.pin_init_cfg = new_cfg
        controller_category.save()

        # THEN
        refreshed = ControllerCategory.objects.get(pk=controller_category.pk)
        assert refreshed.pin_init_cfg == new_cfg

    def test_pin_init_cfg_accepts_nested_json(self):
        """
        GIVEN: a nested JSON structure as pin_init_cfg
        WHEN: creating a ControllerCategory with this configuration
        THEN: the nested structure is stored and retrieved correctly
        """
        # GIVEN
        nested_cfg = {"settings": {"mode": "output", "options": {"pull": "none", "value": 0}}}

        # WHEN
        category = ControllerCategory.objects.create(
            name="Advanced Controller",
            pin_init_cfg=nested_cfg,
        )

        # THEN
        refreshed = ControllerCategory.objects.get(pk=category.pk)
        assert refreshed.pin_init_cfg == nested_cfg


@pytest.mark.django_db
class TestControllerCategoryRelations:
    """Tests for ControllerCategory reverse relation to Controller."""

    def test_controllers_reverse_relation_returns_linked_controller(self, controller, controller_category):
        """
        GIVEN: a Controller linked to a ControllerCategory
        WHEN: accessing the controllers reverse relation on the category
        THEN: the related Controller is returned
        """
        # GIVEN - fixtures create the Controller linked to the category

        # WHEN
        related = controller_category.controllers.all()

        # THEN
        assert related.count() == 1
        assert controller in related

    def test_controllers_reverse_relation_is_empty_when_no_controllers(self, controller_category):
        """
        GIVEN: a ControllerCategory with no Controllers
        WHEN: accessing the controllers reverse relation
        THEN: an empty queryset is returned
        """
        # GIVEN - no Controller is created

        # WHEN
        related = controller_category.controllers.all()

        # THEN
        assert related.count() == 0


@pytest.mark.django_db
class TestControllerCategoryDeletion:
    """Tests for ControllerCategory deletion behavior."""

    def test_delete_category_without_controllers(self, controller_category):
        """
        GIVEN: a ControllerCategory with no Controllers
        WHEN: deleting the ControllerCategory
        THEN: the ControllerCategory is removed from the database
        """
        # GIVEN
        category_id = controller_category.pk

        # WHEN
        controller_category.delete()

        # THEN
        assert not ControllerCategory.objects.filter(pk=category_id).exists()

    def test_delete_category_raises_protected_error_when_controllers_exist(self, controller, controller_category):
        """
        GIVEN: a ControllerCategory that has at least one Controller
        WHEN: attempting to delete the ControllerCategory
        THEN: a ProtectedError is raised and the Controller is preserved
        """
        # GIVEN - fixture creates a Controller linked to the category

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            controller_category.delete()

        assert Controller.objects.filter(pk=controller.pk).exists()


# ─── Controller Tests ──────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestControllerCreation:
    """Tests for Controller model creation."""

    def test_create_controller_with_all_fields(self, controller_category, device, pin):
        """
        GIVEN: a name, a ControllerCategory, a Device and a Pin
        WHEN: creating a Controller with all required fields
        THEN: the Controller is created with the correct values
        """
        # GIVEN / WHEN
        ctrl = Controller.objects.create(
            name="Main Relay",
            category=controller_category,
            device=device,
            pin=pin,
        )

        # THEN
        assert ctrl.pk is not None
        assert ctrl.name == "Main Relay"
        assert ctrl.category == controller_category
        assert ctrl.device == device
        assert ctrl.pin == pin

    def test_create_multiple_controllers_for_same_device(self, controller_category, device, channel):
        """
        GIVEN: a Device with multiple Pins and a ControllerCategory
        WHEN: creating multiple Controllers linked to the same Device
        THEN: all Controllers are persisted in the database
        """
        # GIVEN
        pin1 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=2)
        pin2 = Pin.objects.create(device=device, channel_choiced=channel, pin_number=3)

        # WHEN
        Controller.objects.create(name="Relay 1", category=controller_category, device=device, pin=pin1)
        Controller.objects.create(name="Relay 2", category=controller_category, device=device, pin=pin2)

        # THEN
        assert Controller.objects.count() == 2


@pytest.mark.django_db
class TestControllerRelations:
    """Tests for Controller foreign key relationships."""

    def test_category_relation_returns_correct_category(self, controller, controller_category):
        """
        GIVEN: a Controller linked to a ControllerCategory
        WHEN: accessing the category attribute
        THEN: the correct ControllerCategory is returned
        """
        # GIVEN - fixture creates the Controller with the category

        # WHEN
        result = controller.category

        # THEN
        assert result == controller_category

    def test_device_relation_returns_correct_device(self, controller, device):
        """
        GIVEN: a Controller linked to a Device
        WHEN: accessing the device attribute
        THEN: the correct Device is returned
        """
        # GIVEN - fixture creates the Controller with the device

        # WHEN
        result = controller.device

        # THEN
        assert result == device

    def test_pin_relation_returns_correct_pin(self, controller, pin):
        """
        GIVEN: a Controller linked to a Pin
        WHEN: accessing the pin attribute
        THEN: the correct Pin is returned
        """
        # GIVEN - fixture creates the Controller with the pin

        # WHEN
        result = controller.pin

        # THEN
        assert result == pin

    def test_device_reverse_relation_includes_controller(self, controller, device):
        """
        GIVEN: a Controller linked to a Device
        WHEN: accessing the controllers reverse relation on the Device
        THEN: the related Controller is returned
        """
        # GIVEN - fixture creates the Controller linked to the device

        # WHEN
        related = device.controllers.all()

        # THEN
        assert related.count() == 1
        assert controller in related

    def test_pin_reverse_relation_includes_controller(self, controller, pin):
        """
        GIVEN: a Controller linked to a Pin
        WHEN: accessing the controllers reverse relation on the Pin
        THEN: the related Controller is returned
        """
        # GIVEN - fixture creates the Controller linked to the pin

        # WHEN
        related = pin.controllers.all()

        # THEN
        assert related.count() == 1
        assert controller in related


@pytest.mark.django_db
class TestControllerProtect:
    """Tests for Controller PROTECT behavior on related object deletion."""

    def test_delete_category_raises_protected_error(self, controller, controller_category):
        """
        GIVEN: a Controller linked to a ControllerCategory
        WHEN: attempting to delete the ControllerCategory
        THEN: a ProtectedError is raised and the Controller is preserved
        """
        # GIVEN - fixture creates the Controller linked to the category

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            controller_category.delete()

        assert Controller.objects.filter(pk=controller.pk).exists()

    def test_delete_device_raises_protected_error(self, controller, device):
        """
        GIVEN: a Controller linked to a Device
        WHEN: attempting to delete the Device
        THEN: a ProtectedError is raised and the Controller is preserved
        """
        # GIVEN - fixture creates the Controller linked to the device

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            device.delete()

        assert Controller.objects.filter(pk=controller.pk).exists()

    def test_delete_pin_raises_protected_error(self, controller, pin):
        """
        GIVEN: a Controller linked to a Pin
        WHEN: attempting to delete the Pin
        THEN: a ProtectedError is raised and the Controller is preserved
        """
        # GIVEN - fixture creates the Controller linked to the pin

        # WHEN / THEN
        with pytest.raises(ProtectedError):
            pin.delete()

        assert Controller.objects.filter(pk=controller.pk).exists()


@pytest.mark.django_db
class TestControllerUpdate:
    """Tests for Controller model update operations."""

    def test_update_name(self, controller):
        """
        GIVEN: an existing Controller
        WHEN: updating its name
        THEN: the name is modified correctly in the database
        """
        # GIVEN
        new_name = "Updated Relay"

        # WHEN
        controller.name = new_name
        controller.save()

        # THEN
        updated = Controller.objects.get(pk=controller.pk)
        assert updated.name == new_name

    def test_update_category(self, controller):
        """
        GIVEN: an existing Controller and a new ControllerCategory
        WHEN: assigning the new category to the Controller
        THEN: the category FK is updated correctly in the database
        """
        # GIVEN
        new_category = ControllerCategory.objects.create(name="Motor Controller")

        # WHEN
        controller.category = new_category
        controller.save()

        # THEN
        updated = Controller.objects.get(pk=controller.pk)
        assert updated.category == new_category

    def test_update_pin(self, controller, device, channel):
        """
        GIVEN: an existing Controller and a new Pin on the same Device
        WHEN: assigning the new Pin to the Controller
        THEN: the pin FK is updated correctly in the database
        """
        # GIVEN
        new_pin = Pin.objects.create(device=device, channel_choiced=channel, pin_number=5)

        # WHEN
        controller.pin = new_pin
        controller.save()

        # THEN
        updated = Controller.objects.get(pk=controller.pk)
        assert updated.pin == new_pin


@pytest.mark.django_db
class TestControllerDeletion:
    """Tests for Controller model deletion."""

    def test_delete_controller(self, controller):
        """
        GIVEN: an existing Controller
        WHEN: deleting this Controller
        THEN: the Controller no longer exists in the database
        """
        # GIVEN
        controller_id = controller.pk

        # WHEN
        controller.delete()

        # THEN
        assert not Controller.objects.filter(pk=controller_id).exists()

    def test_delete_controller_does_not_delete_category(self, controller, controller_category):
        """
        GIVEN: an existing Controller linked to a ControllerCategory
        WHEN: deleting the Controller
        THEN: the ControllerCategory is not deleted
        """
        # GIVEN
        category_id = controller_category.pk

        # WHEN
        controller.delete()

        # THEN
        assert ControllerCategory.objects.filter(pk=category_id).exists()

    def test_delete_controller_does_not_delete_device(self, controller, device):
        """
        GIVEN: an existing Controller linked to a Device
        WHEN: deleting the Controller
        THEN: the Device is not deleted
        """
        # GIVEN
        device_id = device.pk

        # WHEN
        controller.delete()

        # THEN
        assert Device.objects.filter(pk=device_id).exists()

    def test_delete_controller_does_not_delete_pin(self, controller, pin):
        """
        GIVEN: an existing Controller linked to a Pin
        WHEN: deleting the Controller
        THEN: the Pin is not deleted
        """
        # GIVEN
        pin_id = pin.pk

        # WHEN
        controller.delete()

        # THEN
        assert Pin.objects.filter(pk=pin_id).exists()
