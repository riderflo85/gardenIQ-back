from django.db import models

from gardeniq.base.models import DescriptionMixinModel
from gardeniq.base.models import ProtectedDeletedMixinModel
from gardeniq.base.models import ProtectedDisabledMixinModel
from gardeniq.base.models import SlugMixinModel


class Argument(
    DescriptionMixinModel,
    SlugMixinModel,
    ProtectedDisabledMixinModel,
    ProtectedDeletedMixinModel,
):
    """
    Inherited fields:
      - `description`
      - `slug`
      - `is_enable`
    """

    VALUES_TYPE_CHOICES = (
        ("int", "integer"),
        ("float", "float"),
        ("str", "string"),
        ("bool", "boolean"),
        ("list", "list"),
        ("none", "none"),
    )

    value_type = models.CharField(
        max_length=5,
        choices=VALUES_TYPE_CHOICES,
        verbose_name="value type",
        help_text="A value type of a argument.",
    )
    required = models.BooleanField(
        default=True,
        verbose_name="required",
        help_text="Define if this argument is required or not to the order.",
    )
    is_option = models.BooleanField(
        default=False, verbose_name="is option", help_text="A option is a argument without value like `--verbose`."
    )

    class Meta:
        verbose_name = "argument"
        verbose_name_plural = "arguments"
        # It's a custom meta attribut to define available fields to send with LG_INIT frame type.
        fields_for_frame = (
            "pk",
            "slug",
            "value_type",
            "required",
            "is_option",
        )

    def __str__(self) -> str:
        return f"Argument `{self.slug}` {self.if_enabled()}"
