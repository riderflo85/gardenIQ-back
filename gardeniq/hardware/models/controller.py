from django.db import models

from gardeniq.base.models import NameMixinModel

from .device import Device
from .mixins import PinInitConfigMixin
from .pin import Pin


class ControllerCategory(PinInitConfigMixin, NameMixinModel):
    """
    Inherited fields:
      - `name`
      - `pin_init_cfg`
    """

    class Meta:
        verbose_name = "controller category"
        verbose_name_plural = "controller categories"


class Controller(NameMixinModel):
    """
    Inherited fields:
      - `name`
    """

    category = models.ForeignKey(
        ControllerCategory,
        on_delete=models.PROTECT,
        related_name="controllers",
        verbose_name="controller category",
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="controllers",
        verbose_name="device",
    )
    pin = models.ForeignKey(
        Pin,
        on_delete=models.PROTECT,
        related_name="controllers",
        verbose_name="pin",
    )

    class Meta:
        verbose_name = "controller"
        verbose_name_plural = "controllers"
