from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.db.models import ProtectedError

import pytest

from gardeniq.base.models import Status
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory

VALID_PIN_INIT_CFG = {"c": "Pin", "a": {"id": "@pin"}}

# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def device_status(db):
    return Status.objects.create(name="Generic", tag="device-generic", color="#123456")


@pytest.fixture
def device_category(db):
    return DeviceCategory.objects.create(
        name="Test Category",
        pins_configuration={"available_channels": [], "digits": [], "pwms": [], "analogs": []},
    )


@pytest.fixture
def device(device_status, device_category):
    return Device.objects.create(
        name="Test Device",
        uid="AABBCCDDEEFF0011",
        path="/dev/ttyUSB0",
        status=device_status,
        category=device_category,
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
    return ControllerCategory.objects.create(name="Relay", pin_init_cfg=VALID_PIN_INIT_CFG)


@pytest.fixture
def controller(controller_category, device, pin):
    return Controller.objects.create(
        name="Main Relay",
        category=controller_category,
        pin=pin,
    )


# ─── ControllerCategory Tests ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestControllerCategoryCreation:
    """Tests for ControllerCategory model creation."""

    def test_create_with_default_seeder_fields(self):
        """
        GIVEN: a name and a valid pin_init_cfg
        WHEN: creating a ControllerCategory without seeder fields
        THEN: is_ready defaults to True and seed_id to None
        """
        # GIVEN / WHEN
        category = ControllerCategory.objects.create(name="Relay", pin_init_cfg=VALID_PIN_INIT_CFG)

        # THEN
        assert category.pk is not None
        assert category.name == "Relay"
        assert category.is_ready is True
        assert category.seed_id is None

    def test_create_with_custom_pin_init_cfg(self):
        """
        GIVEN: a name and a custom pin_init_cfg dict
        WHEN: creating a ControllerCategory with this configuration
        THEN: the ControllerCategory is created with the provided configuration
        """
        # GIVEN
        cfg = {"c": "PWM", "a": {"dest": "@pin", "freq": 1000}}

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
            ControllerCategory.objects.create(name=name, pin_init_cfg=VALID_PIN_INIT_CFG)

        # THEN
        assert ControllerCategory.objects.count() == len(names)


@pytest.mark.django_db
class TestControllerCategoryPinInitCfg:
    """Tests for ControllerCategory pin_init_cfg field."""

    def test_save_rejects_missing_pin_init_cfg(self):
        """
        GIVEN: no pin_init_cfg value
        WHEN: creating a ControllerCategory
        THEN: a ValidationError is raised on pin_init_cfg (the field has no default)
        """
        # WHEN / THEN
        with pytest.raises(ValidationError) as exc_info:
            ControllerCategory.objects.create(name="Relay")
        assert "pin_init_cfg" in exc_info.value.message_dict

    def test_pin_init_cfg_can_be_updated(self, controller_category):
        """
        GIVEN: an existing ControllerCategory
        WHEN: updating the pin_init_cfg with new values
        THEN: the new configuration is persisted correctly
        """
        # GIVEN
        new_cfg = {"c": "PWM", "a": {"dest": "@pin", "freq": 1000, "duty_u16": 512}}

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
        nested_cfg = {"c": "Pin", "a": {"id": "@pin", "mode": "@:OUT", "opts": {"pull": [1, 2], "value": None}}}

        # WHEN
        category = ControllerCategory.objects.create(
            name="Advanced Controller",
            pin_init_cfg=nested_cfg,
        )

        # THEN
        refreshed = ControllerCategory.objects.get(pk=category.pk)
        assert refreshed.pin_init_cfg == nested_cfg

    @pytest.mark.parametrize(
        "cfg",
        [
            pytest.param({}, id="empty"),
            pytest.param({"c": "Pin"}, id="missing-a"),
            pytest.param({"a": {"id": "@pin"}}, id="missing-c"),
            pytest.param({"c": "I2C", "a": {"id": "@pin"}}, id="class-not-whitelisted"),
            pytest.param({"c": "Pin", "a": {"id": "@pin"}, "x": 1}, id="extra-key"),
            pytest.param({"c": "Pin", "a": {"id": 4}}, id="no-pin-reference"),
            pytest.param({"c": "Pin", "a": {"id": "@pin", "mode": "@foo"}}, id="unknown-reference"),
            pytest.param({"c": "Pin", "a": {"id": "@pin", "mode": "@:in"}}, id="lowercase-constant"),
            pytest.param({"c": "Pin", "a": {"id": "@pin", "name": "a b"}}, id="space-in-value"),
            pytest.param({"c": "Pin", "a": {"id": "@pin", "my arg": 1}}, id="space-in-arg-name"),
            pytest.param({"c": "Pin", "a": {"id": "@pin", "opts": {"k": ["a;b"]}}}, id="semicolon-nested"),
            pytest.param({"c": "Pin", "a": {"id": "@pin", "opts": {"a\nb": 1}}}, id="newline-nested-key"),
        ],
    )
    def test_save_rejects_invalid_pin_init_cfg(self, cfg):
        """
        GIVEN: a pin_init_cfg that does not match PIN_INIT_CONFIG_JSON_SCHEMA
        WHEN: creating a ControllerCategory
        THEN: a ValidationError is raised on pin_init_cfg and nothing is saved
        """
        # WHEN / THEN
        with pytest.raises(ValidationError) as exc_info:
            ControllerCategory.objects.create(name="Relay", pin_init_cfg=cfg)
        assert "pin_init_cfg" in exc_info.value.message_dict
        assert ControllerCategory.objects.count() == 0

    def test_full_clean_rejects_invalid_pin_init_cfg(self):
        """
        GIVEN: an unsaved ControllerCategory with an invalid pin_init_cfg
        WHEN: calling full_clean(), as model forms (Django admin) do
        THEN: a ValidationError is raised on the pin_init_cfg field only
        """
        # GIVEN
        category = ControllerCategory(name="Relay", pin_init_cfg={"c": "Pin", "a": {"id": 4}})

        # WHEN / THEN
        with pytest.raises(ValidationError) as exc_info:
            category.full_clean()
        assert list(exc_info.value.message_dict) == ["pin_init_cfg"]

    def test_save_rejects_invalid_pin_init_cfg_on_update(self, controller_category):
        """
        GIVEN: an existing ControllerCategory
        WHEN: saving it with an invalid pin_init_cfg
        THEN: a ValidationError is raised and the stored value is unchanged
        """
        # GIVEN
        controller_category.pin_init_cfg = {"c": "Pin", "a": {}}

        # WHEN / THEN
        with pytest.raises(ValidationError):
            controller_category.save()
        assert ControllerCategory.objects.get(pk=controller_category.pk).pin_init_cfg == VALID_PIN_INIT_CFG


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
            pin=pin,
        )

        # THEN
        assert ctrl.pk is not None
        assert ctrl.name == "Main Relay"
        assert ctrl.category == controller_category
        assert ctrl.pin.device == device
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
        Controller.objects.create(name="Relay 1", category=controller_category, pin=pin1)
        Controller.objects.create(name="Relay 2", category=controller_category, pin=pin2)

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
        GIVEN: a Controller linked to a Pin of a Device
        WHEN: accessing the device of its pin
        THEN: the correct Device is returned
        """
        # GIVEN - fixture creates the Controller with a pin of the device

        # WHEN
        result = controller.pin.device

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
        WHEN: filtering the Controllers by the device of their pin
        THEN: the related Controller is returned
        """
        # GIVEN - fixture creates the Controller linked to a pin of the device

        # WHEN
        related = Controller.objects.filter(pin__device=device)

        # THEN
        assert related.count() == 1
        assert controller in related

    def test_pin_reverse_relation_includes_controller(self, controller, pin):
        """
        GIVEN: a Controller linked to a Pin
        WHEN: accessing the controller reverse one-to-one relation on the Pin
        THEN: the related Controller is returned
        """
        # GIVEN - fixture creates the Controller linked to the pin

        # WHEN
        related = pin.controller

        # THEN
        assert related == controller


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
        new_category = ControllerCategory.objects.create(name="Motor Controller", pin_init_cfg=VALID_PIN_INIT_CFG)

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


# ─── Pin owner ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestControllerPinOwner:
    """Tests for the rule: a Pin is used by one Sensor or Controller only."""

    @pytest.fixture
    def other_owner(self, pin):
        category = SensorCategory.objects.create(name="Other", pin_init_cfg=VALID_PIN_INIT_CFG)
        return Sensor.objects.create(name="Other owner", category=category, pin=pin)

    def test_save_rejects_pin_used_by_another_controller(self, controller, controller_category, pin):
        """
        GIVEN: a Pin already used by a Controller
        WHEN: creating a second Controller on the same Pin
        THEN: the database refuses it
        """
        # GIVEN - fixture creates the Controller on the pin

        # WHEN / THEN
        with pytest.raises(IntegrityError), transaction.atomic():
            Controller.objects.create(name="Second", category=controller_category, pin=pin)

    def test_full_clean_rejects_pin_used_by_another_controller(self, controller, controller_category, pin):
        """
        GIVEN: a Pin already used by a Controller
        WHEN: validating a second Controller on the same Pin
        THEN: a ValidationError is raised on the pin field
        """
        # GIVEN
        second = Controller(name="Second", category=controller_category, pin=pin)

        # WHEN / THEN
        with pytest.raises(ValidationError) as exc:
            second.full_clean()
        assert "pin" in exc.value.message_dict

    def test_save_rejects_pin_used_by_a_sensor(self, other_owner, controller_category, pin):
        """
        GIVEN: a Pin already used by a Sensor
        WHEN: creating a Controller on the same Pin
        THEN: a ValidationError is raised on the pin field and nothing is saved
        """
        # GIVEN - fixture creates the Sensor on the pin

        # WHEN / THEN
        with pytest.raises(ValidationError) as exc:
            Controller.objects.create(name="Controller", category=controller_category, pin=pin)
        assert "pin" in exc.value.message_dict
        assert Controller.objects.count() == 0

    def test_full_clean_rejects_pin_used_by_a_sensor(self, other_owner, controller_category, pin):
        """
        GIVEN: a Pin already used by a Sensor
        WHEN: validating a Controller on the same Pin
        THEN: a ValidationError is raised on the pin field
        """
        # GIVEN
        obj = Controller(name="Controller", category=controller_category, pin=pin)

        # WHEN / THEN
        with pytest.raises(ValidationError) as exc:
            obj.full_clean()
        assert "pin" in exc.value.message_dict

    def test_save_keeps_its_own_pin(self, controller, pin):
        """
        GIVEN: an existing Controller
        WHEN: saving it again without changing its Pin
        THEN: the save succeeds
        """
        # GIVEN
        controller.name = "Renamed"

        # WHEN
        controller.full_clean()
        controller.save()

        # THEN
        controller.refresh_from_db()
        assert controller.name == "Renamed"
        assert controller.pin == pin
