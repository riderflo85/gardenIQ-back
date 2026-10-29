from typing import List

from django.conf import settings
from django.contrib import admin
from django.db.models import Model
from django.forms import ModelForm
from django.forms import TypedChoiceField
from django.http import HttpRequest

from gardeniq.base.admin import seeder_fields_name
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory
from gardeniq.hardware.utils import list_connected_devices

# Help texts shown under the JSON fields in the admin forms (rendered as HTML by the admin templates).
PINS_CONFIGURATION_HELP_TEXT = (
    "Datasheet of the card, as a JSON object. Required keys: <code>available_channels</code> (list of channel "
    "type names), <code>digits</code>, <code>pwms</code>, <code>analogs</code>. Optional keys: <code>i2cs</code>, "
    "<code>spis</code>, <code>uarts</code>.<br>"
    'Each channel type is a list of channels <code>{"name": "GP0", "pins": [0]}</code> with integer pins: '
    "1 pin for digits, pwms and analogs, 2 for i2cs and uarts, 4 for spis.<br>"
    'Example: <code>{"available_channels": ["digit"], "digits": [{"name": "GP0", "pins": [0]}], '
    '"pwms": [], "analogs": []}</code>'
)
PIN_INIT_CFG_HELP_TEXT = (
    "How the card instantiates the MicroPython object of the pin, as a JSON object with only two keys: "
    "<code>c</code>, the class (<code>Pin</code>, <code>ADC</code> or <code>PWM</code>), and <code>a</code>, "
    'the constructor arguments as <code>{"name": value}</code>.<br>'
    'Values: <code>"@pin"</code> is the pin number (required at least once), <code>"@:NAME"</code> is the '
    'constant NAME of the class <code>c</code> (upper case, e.g. <code>"@:IN"</code>), anything else is sent '
    "as is. No space, tab, new line or <code>;</code> in strings.<br>"
    'Examples: <code>{"c": "Pin", "a": {"id": "@pin", "mode": "@:IN"}}</code>, '
    '<code>{"c": "PWM", "a": {"dest": "@pin", "freq": 1000, "duty_u16": 512}}</code>'
)


class JSONHelpTextAdminMixin:
    """Add `json_help_texts` ({field name: HTML help text}) under the JSON fields of the admin form."""

    json_help_texts: dict[str, str] = {}

    def get_form(self, request: HttpRequest, obj: Model | None = None, **kwargs) -> type[ModelForm]:
        kwargs["help_texts"] = {**self.json_help_texts, **kwargs.get("help_texts", {})}
        return super().get_form(request, obj, **kwargs)  # pyright: ignore[reportAttributeAccessIssue]


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin interface for the Device model."""

    list_display = (
        "id",
        "name",
        "communication_protocol",
        "uid",
        "path",
        "status",
        "last_seen",
        "gd_firmware_version",
        "mp_firmware_version",
        "need_upgrade",
    )
    search_fields = ("name", "uid", "path")
    list_filter = (
        "status",
        "need_upgrade",
        "gd_firmware_version",
        "mp_firmware_version",
    )
    fieldsets = (
        (
            "Device Information",
            {
                "fields": ("name", "description", "uid", "path"),
            },
        ),
        (
            "Device type",
            {
                "fields": ("category", "communication_protocol"),
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


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(JSONHelpTextAdminMixin, admin.ModelAdmin):
    """Admin interface for the DeviceCategory model."""

    json_help_texts = {"pins_configuration": PINS_CONFIGURATION_HELP_TEXT}

    list_display = ("id", "name", "description") + seeder_fields_name
    search_fields = ("name",) + seeder_fields_name
    list_filter = ("name",) + seeder_fields_name


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    """Admin interface for the Channel model."""

    list_display = ("id", "name", "description")
    search_fields = ("name",)


@admin.register(Pin)
class PinAdmin(admin.ModelAdmin):
    """Admin interface for the Pin model."""

    list_display = ("id", "pin_number", "channel_choiced", "device")
    search_fields = ("pin_number",)
    list_filter = ("channel_choiced", "device")


@admin.register(ControllerCategory)
class ControllerCategoryAdmin(JSONHelpTextAdminMixin, admin.ModelAdmin):
    """Admin interface for the ControllerCategory model."""

    json_help_texts = {"pin_init_cfg": PIN_INIT_CFG_HELP_TEXT}

    list_display = ("id", "name") + seeder_fields_name
    search_fields = ("name",) + seeder_fields_name


@admin.register(SensorCategory)
class SensorCategoryAdmin(JSONHelpTextAdminMixin, admin.ModelAdmin):
    """Admin interface for the SensorCategory model."""

    json_help_texts = {"pin_init_cfg": PIN_INIT_CFG_HELP_TEXT}

    list_display = ("id", "name", "unity_value") + seeder_fields_name
    search_fields = ("name",) + seeder_fields_name


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    """Admin interface for the Sensor model."""

    list_display = ("id", "name", "category", "pin__device", "pin")
    search_fields = ("name",)
    list_filter = ("category", "pin__device")


@admin.register(Controller)
class ControllerAdmin(admin.ModelAdmin):
    """Admin interface for the Controller model."""

    list_display = ("id", "name", "category", "pin__device", "pin")
    search_fields = ("name",)
    list_filter = ("category", "pin__device")
