from django.db import models

from gardeniq.base.models import NameMixinModel
from gardeniq.base.models import OptionalDescriptionMixinModel


class Status(NameMixinModel, OptionalDescriptionMixinModel):
    """
    Inherited fields:
      - `name`
      - `description`:optional
    """
    DEFAULT_COLOR = "#A2A2A2"

    tag = models.SlugField(verbose_name="tag", help_text="A tag of this status. (Like category).")
    color = models.CharField(max_length=7, default=DEFAULT_COLOR, verbose_name="color")

    def __str__(self) -> str:
        return f"Status `{self.name}` : {self.tag}"
