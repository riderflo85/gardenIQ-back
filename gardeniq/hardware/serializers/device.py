from typing import List

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from gardeniq.base.models import Status
from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import OptionalDescriptionMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SeederIsReadyMixinSerializer
from gardeniq.base.serializers import SeederMixinSerializer
from gardeniq.base.serializers import StatusReadOnlySerializer
from gardeniq.base.serializers import StatusSerializer
from gardeniq.base.serializers.mixins import PKMixinSerializer
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.utils import list_connected_devices
from gardeniq.hardware.validations import jsonschema_validation


def get_serial_port_choices() -> List[str]:
    serial_ports = list_connected_devices(settings.LD_FORMATS.LIST_DEVICES)
    return [f"/dev/{s_p}" for s_p in serial_ports]


class DeviceCategorySerializer(
    BaseSerializer,
    NameMixinSerializer,
    OptionalDescriptionMixinSerializer,
    SeederIsReadyMixinSerializer,
):
    pins_configuration = serializers.JSONField()
    # Override is_ready field to be read-only and default to True
    is_ready = serializers.BooleanField(read_only=True, default=True)

    class Meta:
        model = DeviceCategory

    def validate_pins_configuration(self, value: dict) -> dict:
        """
        Validate the pins_configuration JSON field against the DATASHEET_JSON_SCHEMA defined in settings.

        Args:
            value (dict): The pins_configuration JSON data to validate.
        """
        try:
            jsonschema_validation(value, settings.DATASHEET_JSON_SCHEMA, "pins_configuration")
        except DjangoValidationError as e:
            # Convert Django ValidationError to DRF ValidationError.
            raise serializers.ValidationError(e.message_dict)
        return value


class DeviceCategoryListReadOnlySerializer(ReadOnlySerializer, DeviceCategorySerializer):
    pins_configuration = None  # Hide pins_configuration in list view


class DeviceCategoryDetailReadOnlySerializer(ReadOnlySerializer, DeviceCategorySerializer):
    pass


class DeviceCategorySeederSerializer(SeederMixinSerializer, DeviceCategorySerializer):
    pass


class DeviceSerializer(BaseSerializer, NameMixinSerializer, OptionalDescriptionMixinSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=DeviceCategory.objects.all())
    uid = serializers.CharField(max_length=32, read_only=True)
    communication_protocol = serializers.ChoiceField(choices=Device.AVAILABLE_COMM_PROTOCOLS)
    path = serializers.ChoiceField(choices=[], required=False)  # Initialize empty to fill in `__init__`
    last_seen = serializers.DateTimeField(read_only=True)
    status = serializers.PrimaryKeyRelatedField(queryset=Status.objects.all(), many=False)
    gd_firmware_version = serializers.CharField(read_only=True)
    mp_firmware_version = serializers.CharField(read_only=True)
    need_upgrade = serializers.BooleanField(read_only=True)

    class Meta:
        model = Device

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["path"].choices = get_serial_port_choices()


class DeviceListReadOnlySerializer(ReadOnlySerializer, DeviceSerializer):
    uid = None  # Hide uid in list view
    category = DeviceCategoryListReadOnlySerializer(read_only=True)
    status = StatusSerializer(read_only=True)


class DeviceDetailReadOnlySerializer(ReadOnlySerializer, DeviceSerializer):
    category = DeviceCategoryDetailReadOnlySerializer(read_only=True)
    status = StatusSerializer(read_only=True)


class DeviceMinimalReadOnlySerializer(ReadOnlySerializer, PKMixinSerializer, NameMixinSerializer):
    status = StatusReadOnlySerializer()
