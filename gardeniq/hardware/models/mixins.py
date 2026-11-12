from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from gardeniq.hardware.validations import jsonschema_validation

from .pin import Pin


class PinInitConfigMixin(models.Model):
    """
    Mixin for models that have a pin_init_cfg field.
    """

    pin_init_cfg = models.JSONField(
        verbose_name="pin init configuration",
        help_text="Initial configuration for the pins.",
    )

    class Meta:
        abstract = True

    def clean(self) -> None:
        """
        Validate the pin_init_cfg JSON field against the PIN_INIT_CONFIG_JSON_SCHEMA during `full_clean()`,
        so that model forms (Django admin) display the error on the field instead of failing in `save()`.

        Raises:
            ValidationError: If the pin_init_cfg does not conform to the schema.
        """
        super().clean()
        # None means the form has already reported the field as missing or malformed.
        if self.pin_init_cfg is not None:
            jsonschema_validation(self.pin_init_cfg, settings.PIN_INIT_CONFIG_JSON_SCHEMA, "pin_init_cfg")

    def save(self, *args, **kwargs) -> None:
        """
        Override the save method to validate the pin_init_cfg JSON field against
        the PIN_INIT_CONFIG_JSON_SCHEMA defined in settings before saving the instance.

        Raises:
            ValidationError: If the pin_init_cfg does not conform to the schema.
        """
        jsonschema_validation(self.pin_init_cfg, settings.PIN_INIT_CONFIG_JSON_SCHEMA, "pin_init_cfg")
        super().save(*args, **kwargs)


class PinOwnerMixin(models.Model):
    """
    Mixin for models wired to a device pin (Sensor, Controller).
    The device is read from `pin.device`, and a pin belongs to one owner only, across all owner models.
    """

    # Reverse accessors on Pin of every owner model (related_name="%(class)s").
    PIN_OWNERS: tuple[str, ...] = ("sensor", "controller")

    pin = models.OneToOneField(
        Pin,
        on_delete=models.PROTECT,
        related_name="%(class)s",
        verbose_name="pin",
    )

    class Meta:
        abstract = True

    def _check_pin_is_free(self) -> None:
        """
        Check that the pin is not already used by an owner of another model.
        The uniqueness inside the same model is enforced by the database (one-to-one).

        Raises:
            ValidationError: If the pin is already used by another owner model.
        """
        if self.pin_id is None:  # pyright: ignore[reportAttributeAccessIssue]
            return
        for owner in self.PIN_OWNERS:
            if owner != self._meta.model_name and hasattr(self.pin, owner):
                raise ValidationError({"pin": f"Pin {self.pin.pin_number} is already used by a {owner}."})

    def clean(self) -> None:
        super().clean()
        self._check_pin_is_free()

    def save(self, *args, **kwargs) -> None:
        self._check_pin_is_free()
        super().save(*args, **kwargs)
