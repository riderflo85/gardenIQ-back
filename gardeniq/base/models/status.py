from django.db import models

from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import OptionalDescriptionMixinModel
from gardeniq.base.models import SeederMixinModel


class Status(NameMixinModel, OptionalDescriptionMixinModel, SeederMixinModel):
    """
    Inherited fields:
      - `name`
      - `description`:optional
      - `seed_id`
      - `is_ready`
    """

    DEFAULT_COLOR = "#A2A2A2"

    tag = models.SlugField(verbose_name="tag", help_text="A tag of this status. (Like category).")
    color = models.CharField(max_length=7, default=DEFAULT_COLOR, verbose_name="color")

    class Meta:
        verbose_name = "status"
        verbose_name_plural = "statuses"

    def __str__(self) -> str:
        return f"Status `{self.name}` : {self.tag}"
