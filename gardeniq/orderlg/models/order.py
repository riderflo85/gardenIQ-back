from typing import Any

from django.db import models

from gardeniq.base.models import DescriptionMixinModel
from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import ProtectedDeletedMixinModel
from gardeniq.base.models import ProtectedDisabledMixinModel
from gardeniq.base.models import SlugMixinModel


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

    class Meta:
        verbose_name = "order"
        verbose_name_plural = "orders"

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
