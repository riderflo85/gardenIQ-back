from typing import Optional

from django.db import models
from django.utils.text import slugify

from gardeniq.base.exceptions import DeleteProtectedException
from gardeniq.base.exceptions import DisabledProtectedException

from .custom_managers import DisabledManager
from .custom_managers import EnabledManager


class SlugMixinModel(models.Model):
    slug = models.SlugField(
        unique=True,
        verbose_name="slug",
        help_text="A slug is a short label for something, containing only letters, numbers, underscores or hyphens.",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Override the `save` method to prepopulated slug field."""
        if self.slug in ("", None):
            self.slug = self.generate_slug(self.prepopulated_slug())
        super().save(*args, **kwargs)

    @staticmethod
    def generate_slug(value: str) -> str:
        """Generate a slug value with field value."""
        return slugify(value)

    def prepopulated_slug(self) -> str:
        """
        Generate a slug value with model instance attributes.
        Must be overridden by each model.
        """
        raise NotImplementedError


class DescriptionMixinModel(models.Model):
    description = models.TextField(verbose_name="description")

    class Meta:
        abstract = True


class NameMixinModel(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="name",
    )

    class Meta:
        abstract = True


class ProtectedRelationsMixinModel(models.Model):
    """
    Add a ``get_protected_relations`` method listing all relations depending on this object.
    This method will follow all the reverse relations (i.e. all the relation which depend on the current instance)
    by default, and will also follow forward relations (i.e. many to many fields declared on the model) if specified.

    The following class variables can be defined on any class implementing this mixin
    to widen or narrow the list of relations to consider:

    - ``protected_relations_exclude_models``, a list of models to not consider as protected.
      Each entry is a two with the app label and the model name.
      defaults to ``None``.
    - ``protected_relations_include_m2m``, whether to include the many to many relation declared on the current model,
      defaults to ``False``.
    """

    protected_relations_exclude_models: Optional[list[tuple[str, str]]] = None
    protected_relations_include_m2m: bool = False

    class Meta:
        abstract = True

    def get_protected_relations(self):
        """
        Get information about the relations depending on this object

        :return: information about the relations depending on this object
        """
        # TODO: implement this method !


class ProtectedDisabledMixinModel(ProtectedRelationsMixinModel):

    is_enabled = models.BooleanField(
        default=True,
        verbose_name="is enabled",
        help_text="Designate whether this object is enabled and will show up in searches by default.",
    )

    # Must be declared fisrt.
    # It's the default manager
    objects = models.Manager()

    # Custom managers
    enabled = EnabledManager()
    disabled = DisabledManager()

    class Meta:
        abstract = True

    def enable(self):
        self.is_enabled = True
        self.save()

    def disable(self):
        relations = self.get_protected_relations()
        if relations:
            raise DisabledProtectedException()

        self.is_enabled = False
        self.save()

    def if_enabled(self) -> str:
        """
        Return the string "enabled" if the object is enabled, else "disabled".

        :return: str
        """
        return "enabled" if self.is_enabled else "disabled"


class ProtectedDeletedMixinModel(ProtectedRelationsMixinModel):
    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        relations = self.get_protected_relations()
        if relations:
            raise DeleteProtectedException()

        super().delete(*args, **kwargs)
