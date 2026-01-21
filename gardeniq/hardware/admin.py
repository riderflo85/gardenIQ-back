from typing import List

from django.conf import settings
from django.contrib import admin
from django.forms import TypedChoiceField
from django.http import HttpRequest

from gardeniq.hardware.models import Device
from gardeniq.hardware.utils import list_connected_devices


# Register your models here.
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin interface for the Device model."""

    list_display = (
        "id",
        "name",
        "uid",
        "path",
        "status",
        "last_seen",
        "gd_firmware_version",
        "mp_firmware_version",
        "need_upgrade",
    )
    search_fields = ("name", "uid", "path")
    list_filter = ("status", "need_upgrade", "gd_firmware_version", "mp_firmware_version")
    fieldsets = (
        (
            "Device Information",
            {
                "fields": ("name", "description", "uid", "path"),
            },
        ),
        (
            "Firmware Information",
            {
                "fields": ("gd_firmware_version", "mp_firmware_version", "need_upgrade"),
            },
        ),
        (
            "Status Information",
            {
                "fields": ("status",),
            },
        ),
    )

    def _get_serial_port_choices(self) -> List[tuple[str, str]]:
        serial_ports = list_connected_devices(settings.LD_FORMATS.LIST_DEVICES)
        return [(p, p) for p in serial_ports]

    def get_form(self, request: HttpRequest, obj=None, **kwargs):
        """
        Overrides the default form generation for the admin interface.

        Retrieves the base form using the superclass implementation, then modifies the 'path' field
        to be a TypedChoiceField with choices provided by `_get_serial_port_choices()` and coerced to string.
        This allows dynamic selection of serial ports in the admin form.
        """
        # Get the base form
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["path"] = TypedChoiceField(choices=self._get_serial_port_choices(), coerce=str)  # type: ignore
        return form
