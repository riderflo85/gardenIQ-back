from django.contrib import admin

from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.models import Order


# Register your models here.
@admin.register(Argument)
class ArgumentAdmin(admin.ModelAdmin):
    """Admin interface for the Argument model."""

    list_display = (
        "id",
        "slug",
        "value_type",
        "is_enabled",
        "required",
        "is_option",
    )
    search_fields = ("slug", "value_type")
    list_filter = ("is_enabled", "required", "is_option", "orders")
    # For ordering fields in admin create and update forms.
    fields = (
        "slug",
        "description",
        "value_type",
        "required",
        "is_option",
        "is_enabled",
    )


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
    list_filter = ("action_type", "is_enabled", "arguments")
    # For ordering fields in admin create and update forms.
    fields = (
        "name",
        "slug",
        "description",
        "action_type",
        "arguments",
        "is_enabled",
    )
