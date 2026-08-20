from django.db import models

from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import OptionalDescriptionMixinModel

from .device import Device


class Channel(NameMixinModel, OptionalDescriptionMixinModel):
    """
    Inherited fields:
      - `name`
      - `description`:optional
    """

    class Meta:
        verbose_name = "channel"
        verbose_name_plural = "channels"


class Pin(models.Model):
    """
    Represents a pin on a device.
    """

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="pins",
        verbose_name="device",
    )
    channel_choiced = models.ForeignKey(
        Channel,
        on_delete=models.PROTECT,
        related_name="choiced_pins",
        verbose_name="channel",
    )
    channels_available = models.ManyToManyField(
        Channel,
        related_name="available_pins",
        verbose_name="available channels",
        help_text="Channels that can be assigned to this pin.",
    )
    pin_number = models.PositiveIntegerField(
        verbose_name="pin number",
        help_text="The physical pin number on the device.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["device", "pin_number"],
                name="unique_device_pin_number",
            )
        ]
        verbose_name = "pin"
        verbose_name_plural = "pins"
