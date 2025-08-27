from django.db import models

from gardeniq.base.models import DescriptionMixinModel
from gardeniq.base.models import SlugMixinModel
from gardeniq.base.models import ProtectedDisabledMixinModel
from gardeniq.base.models import ProtectedDeletedMixinModel
from gardeniq.base.models import NameMixinModel


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

    VALUES_CHOICES = (
        ("int", "integer"),
        ("float", "float"),
        ("str", "string"),
        ("bool", "boolean"),
        ("list", "list"),
    )

    value_type = models.CharField(
        max_length=5,
        choices=VALUES_CHOICES,
        verbose_name="value type",
        help_text="A value type of a argument.",
    )
    required = models.BooleanField(
        default=True,
        verbose_name="required",
        help_text="Define if this argument is required or not to the order.",
    )
    is_option = models.BooleanField(
        default=False,
        verbose_name="is option",
        help_text="A option is a argument without value like `--verbose`."
    )

    def __str__(self) -> str:
        is_enabled = super(ProtectedDisabledMixinModel, self).__str__()
        return f"{self.slug} {is_enabled}"


class Order(
    DescriptionMixinModel,
    NameMixinModel,
    SlugMixinModel,
    ProtectedDisabledMixinModel,
    ProtectedDeletedMixinModel,
):
    """
    Inherited fields:
      - `description`
      - `name`
      - `slug`
      - `is_enable`
    """

    ACTIONS_CHOICES = (
        ("get", "getter"),
        ("set", "setter"),
    )

    action_type = models.CharField(
        max_length=10,
        choices=ACTIONS_CHOICES,
        verbose_name="action type",
    )
    arguments = models.ManyToManyField(
        Argument,
        related_name="orders",
        verbose_name="arguments",
        help_text="All the arguments necessary for the command to work."
    )

    def __str__(self) -> str:
        is_enabled = super(ProtectedDisabledMixinModel, self).__str__()
        return f"{self.name} {is_enabled}"
