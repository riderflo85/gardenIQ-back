from django.db import models

from gardeniq.base.models import NameMixinModel

from .device import Device
from .mixins import PinInitConfigMixin
from .pin import Pin


class SensorCategory(PinInitConfigMixin, NameMixinModel):
    """
    Inherited fields:
      - `name`
      - `pin_init_cfg`
    """

    unity_value = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="unity value",
        help_text="Unity value of the sensor category (e.g: '°C', '%', 'lux').",
    )

    class Meta:
        verbose_name = "sensor category"
        verbose_name_plural = "sensor categories"


class Sensor(NameMixinModel):
    """
    Inherited fields:
      - `name`
    """

    category = models.ForeignKey(
        SensorCategory,
        on_delete=models.PROTECT,
        related_name="sensors",
        verbose_name="sensor category",
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="sensors",
        verbose_name="device",
    )
    pin = models.ForeignKey(
        Pin,
        on_delete=models.PROTECT,
        related_name="sensors",
        verbose_name="pin",
    )

    class Meta:
        verbose_name = "sensor"
        verbose_name_plural = "sensors"
