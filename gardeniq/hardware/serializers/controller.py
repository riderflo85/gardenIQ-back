from rest_framework import serializers

from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import MinimalReadOnlySerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin

from .device import DeviceDetailReadOnlySerializer
from .device import DeviceMinimalReadOnlySerializer
from .mixins import PinInitConfigMixinSerializer
from .pin import PinMinimalReadOnlySerializer


class ControllerCategorySerializer(BaseSerializer, NameMixinSerializer, PinInitConfigMixinSerializer):
    class Meta:
        model = ControllerCategory


class ControllerCategoryReadOnlySerializer(ReadOnlySerializer, ControllerCategorySerializer):
    pass


class ControllerSerializer(BaseSerializer, NameMixinSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=ControllerCategory.objects.all())
    device = serializers.PrimaryKeyRelatedField(queryset=Device.objects.all())
    pin = serializers.PrimaryKeyRelatedField(queryset=Pin.objects.all())

    class Meta:
        model = Controller


class ControllerListReadOnlySerializer(ReadOnlySerializer, ControllerSerializer):
    category = MinimalReadOnlySerializer(read_only=True)
    device = DeviceMinimalReadOnlySerializer(read_only=True)
    pin = PinMinimalReadOnlySerializer(read_only=True)


class ControllerDetailReadOnlySerializer(ControllerListReadOnlySerializer):
    device = DeviceDetailReadOnlySerializer(read_only=True)
