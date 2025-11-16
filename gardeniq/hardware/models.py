from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import OptionalDescriptionMixinModel
from gardeniq.base.models import Status
from gardeniq.hardware.protocols.settings import pattern_strict_version


class Device(NameMixinModel, OptionalDescriptionMixinModel):
    """
    Inherited fields:
      - `name`
      - `description`:optional
    """
    uid = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="device uid",
        help_text="Unique device card UID (e.g: '12AB34567890DEAD').",
    )
    path = models.CharField(
        max_length=64,
        validators=[RegexValidator(settings.PATTERN_SERIAL_PORT)],
        verbose_name="card port path",
        help_text="Path of this card.",
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        verbose_name="last seen",
        help_text="Datetime of the last communication.",
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        limit_choices_to=models.Q(tag__icontains="device"),
        related_name="devices",
        verbose_name="status",
    )
    gd_firmware_version = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(pattern_strict_version)],
        verbose_name="GardenIQ firmware version",
    )
    mp_firmware_version = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(pattern_strict_version)],
        verbose_name="MicroPython firmware version",
    )

    def __str__(self) -> str:
        return f"Device `{self.name}` : {self.uid} : {self.path}"
