from django.contrib import admin

from gardeniq.base.admin import seeder_fields_name
from gardeniq.orderlg.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for the Order model."""

    list_display = seeder_fields_name + (
        "id",
        "name",
        "slug",
        "action_type",
        "is_enabled",
    )
    search_fields = ("name", "slug", "action_type")
    list_filter = seeder_fields_name + ("action_type", "is_enabled")
    # For ordering fields in admin create and update forms.
    fields = seeder_fields_name + (
        "name",
        "slug",
        "description",
        "action_type",
        "sensor",
        "controller",
        "is_toggle_ctrl_value",
        "ctrl_value",
        "is_enabled",
    )
