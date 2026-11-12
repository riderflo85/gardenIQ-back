from django.db import models

from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import SeederMixinModel

from .mixins import PinInitConfigMixin
from .mixins import PinOwnerMixin


class ControllerCategory(PinInitConfigMixin, NameMixinModel, SeederMixinModel):
    """
    Inherited fields:
      - `name`
      - `pin_init_cfg`
      - `seed_id`
      - `is_ready`
    """

    class Meta:
        verbose_name = "controller category"
        verbose_name_plural = "controller categories"


class Controller(PinOwnerMixin, NameMixinModel):
    """
    Inherited fields:
      - `pin`
      - `name`
    """

    category = models.ForeignKey(
        ControllerCategory,
        on_delete=models.PROTECT,
        related_name="controllers",
        verbose_name="controller category",
    )

    class Meta:
        verbose_name = "controller"
        verbose_name_plural = "controllers"
