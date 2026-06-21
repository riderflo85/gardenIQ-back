from django.contrib import admin

from gardeniq.orderlg.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for the Order model."""

    list_display = (
        "id",
        "name",
        "slug",
        "action_type",
        "is_enabled",
    )
    search_fields = ("name", "slug", "action_type")
    list_filter = ("action_type", "is_enabled")
    # For ordering fields in admin create and update forms.
    fields = (
        "name",
        "slug",
        "description",
        "action_type",
        "is_enabled",
    )
