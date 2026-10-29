from rest_framework import serializers

from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import MinimalReadOnlySerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SeederIsReadyMixinSerializer
from gardeniq.base.serializers import SeederMixinSerializer
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory

from .device import DeviceDetailReadOnlySerializer
from .device import DeviceMinimalReadOnlySerializer
from .mixins import PinInitConfigMixinSerializer
from .pin import PinMinimalReadOnlySerializer


class SensorCategorySerializer(
    BaseSerializer,
    NameMixinSerializer,
    PinInitConfigMixinSerializer,
    SeederIsReadyMixinSerializer,
):
    unity_value = serializers.CharField(max_length=20)
    # Override is_ready field to be read-only and default to True
    is_ready = serializers.BooleanField(read_only=True, default=True)

    class Meta:
        model = SensorCategory


class SensorCategoryListReadOnlySerializer(ReadOnlySerializer, SensorCategorySerializer):
    pin_init_cfg = None  # Hide pin_init_cfg in list view


class SensorCategoryDetailReadOnlySerializer(ReadOnlySerializer, SensorCategorySerializer):
    pass


class SensorCategorySeederSerializer(SeederMixinSerializer, SensorCategorySerializer):
    pass


class SensorSerializer(BaseSerializer, NameMixinSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=SensorCategory.objects.all())
    device = serializers.PrimaryKeyRelatedField(queryset=Device.objects.all())
    pin = serializers.PrimaryKeyRelatedField(queryset=Pin.objects.all())

    class Meta:
        model = Sensor


class SensorListReadOnlySerializer(ReadOnlySerializer, SensorSerializer):
    category = MinimalReadOnlySerializer(read_only=True)
    device = DeviceMinimalReadOnlySerializer(read_only=True)
    pin = PinMinimalReadOnlySerializer(read_only=True)


class SensorDetailReadOnlySerializer(SensorListReadOnlySerializer):
    device = DeviceDetailReadOnlySerializer(read_only=True)
