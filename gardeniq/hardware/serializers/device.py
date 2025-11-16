from typing import List

from django.conf import settings

from rest_framework import serializers

from gardeniq.base.models import Status
from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import OptionalDescriptionMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import StatusSerializer
from gardeniq.hardware.models import Device
from gardeniq.hardware.utils import list_connected_devices


def get_serial_port_choices() -> List[str]:
    serial_ports = list_connected_devices(settings.LD_FORMATS.LIST_DEVICES)
    return [f"/dev/{s_p}" for s_p in serial_ports]


class DeviceSerializer(BaseSerializer, NameMixinSerializer, OptionalDescriptionMixinSerializer):
    uid = serializers.CharField(max_length=32, read_only=True)
    path = serializers.ChoiceField(choices=[])  # Initialize empty to fill in `__init__`
    last_seen = serializers.DateTimeField(read_only=True)
    status = serializers.PrimaryKeyRelatedField(queryset=Status.objects.all(), many=False)
    gd_firmware_version = serializers.CharField(read_only=True)
    mp_firmware_version = serializers.CharField(read_only=True)

    class Meta:
        model = Device

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["path"].choices = get_serial_port_choices()


class DeviceDetailReadOnlySerializer(ReadOnlySerializer, DeviceSerializer):
    status = StatusSerializer(many=False, read_only=True)
