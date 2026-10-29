from django.conf import settings
from django.db import models

from gardeniq.hardware.validations import jsonschema_validation


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

    def save(self, *args, **kwargs) -> None:
        """
        Override the save method to validate the pin_init_cfg JSON field against
        the PIN_INIT_CONFIG_JSON_SCHEMA defined in settings before saving the instance.

        Raises:
            ValidationError: If the pin_init_cfg does not conform to the schema.
        """
        jsonschema_validation(self.pin_init_cfg, settings.PIN_INIT_CONFIG_JSON_SCHEMA, "pin_init_cfg")
        super().save(*args, **kwargs)
