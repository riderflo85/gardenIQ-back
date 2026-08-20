from django.db import models


class PinInitConfigMixin(models.Model):
    """
    Mixin for models that have a pin_init_cfg field.
    """

    # TODO: Faire la validation avec JSONSchema pour vérifier que le JSON est bien formé et correspond
    # à la structure attendue
    pin_init_cfg = models.JSONField(
        default=dict,
        verbose_name="pin init configuration",
        help_text="Initial configuration for the pins.",
    )

    class Meta:
        abstract = True
