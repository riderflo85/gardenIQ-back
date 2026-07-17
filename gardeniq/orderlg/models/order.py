from typing import Any

from django.db import models
from django.db.models import Q

from gardeniq.base.models import DescriptionMixinModel
from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import ProtectedDeletedMixinModel
from gardeniq.base.models import ProtectedDisabledMixinModel
from gardeniq.base.models import SlugMixinModel
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import Sensor


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
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        null=True,
        related_name="orders",
        verbose_name="sensor",
    )
    controller = models.ForeignKey(
        Controller,
        on_delete=models.CASCADE,
        null=True,
        related_name="orders",
        verbose_name="controller",
    )
    is_toggle_ctrl_value = models.BooleanField(
        default=False,
        verbose_name="is toggle control value",
        help_text="If True, the order will toggle the control value. "
        "If False, the order will set the control value to the specified value.",
    )
    ctrl_value = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="control value",
        help_text="The control value to set. " "If `is_toggle_ctrl_value` is True, this field will be ignored.",
    )

    class Meta:
        verbose_name = "order"
        verbose_name_plural = "orders"
        constraints = [
            models.CheckConstraint(
                condition=(Q(action_type="get") & (Q(sensor__isnull=False) | Q(controller__isnull=False)))
                | (Q(action_type="set") & Q(controller__isnull=False) & Q(sensor__isnull=True)),
                name="check_order_action_type_sensor_controller",
            )
        ]

    def __str__(self) -> str:
        return f"Order `{self.name}` {self.if_enabled()}"

    def prepopulated_slug(self) -> str:
        return self.name

    def register_response_data(self, data: Any) -> None:
        # TODO: register the device response data into log system
        #   OR database telemetry
        #   OR SSE system for display data to user dashboard.
        # e.g: back send `get_temp` order, device response with temp data.
        pass

    def register_ok_response_state(self) -> None:
        # TODO: register the device ok response state into log system
        #   OR database telemetry
        #   OR SSE system for display response state to user dashboard.
        # e.g: back send `open_van 1` order, device response without data. Juste state `ok` or `err`.
        pass
