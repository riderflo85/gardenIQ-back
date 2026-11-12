from django.db import models

from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import SeederMixinModel

from .mixins import PinInitConfigMixin
from .mixins import PinOwnerMixin


class SensorCategory(PinInitConfigMixin, NameMixinModel, SeederMixinModel):
    """
    Inherited fields:
      - `name`
      - `pin_init_cfg`
      - `seed_id`
      - `is_ready`
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


class Sensor(PinOwnerMixin, NameMixinModel):
    """
    Inherited fields:
      - `pin`
      - `name`
    """

    category = models.ForeignKey(
        SensorCategory,
        on_delete=models.PROTECT,
        related_name="sensors",
        verbose_name="sensor category",
    )

    class Meta:
        verbose_name = "sensor"
        verbose_name_plural = "sensors"
