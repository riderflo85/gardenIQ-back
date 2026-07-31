from django.contrib import admin

from gardeniq.base.models import SeederMixinModel
from gardeniq.base.models.status import Status

seeder_fields_name = tuple(field.name for field in SeederMixinModel._meta.fields if field.name != "id")


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    """Admin interface for the Status model."""

    list_display = seeder_fields_name + ("id", "name", "tag", "color", "description")
    search_fields = ("name", "tag")
    list_filter = seeder_fields_name + ("color",)
    # For ordering fields in admin create and update forms.
    fields = list(filter(lambda f: f != "id", list_display))
