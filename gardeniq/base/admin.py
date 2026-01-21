from django.contrib import admin

from gardeniq.base.models.status import Status


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    """Admin interface for the Status model."""

    list_display = ("id", "name", "tag", "color", "description")
    search_fields = ("name", "tag")
    list_filter = ("color",)
    # For ordering fields in admin create and update forms.
    fields = list(filter(lambda f: f != "id", list_display))
