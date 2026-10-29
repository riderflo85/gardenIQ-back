from rest_framework import serializers

from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import MinimalReadOnlySerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SeederIsReadyMixinSerializer
from gardeniq.base.serializers import SeederMixinSerializer
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory

from .device import DeviceDetailReadOnlySerializer
from .device import DeviceMinimalReadOnlySerializer
from .mixins import PinInitConfigMixinSerializer
from .mixins import PinOwnerMixinSerializer
from .pin import PinMinimalReadOnlySerializer


class ControllerCategorySerializer(
    BaseSerializer, NameMixinSerializer, PinInitConfigMixinSerializer, SeederIsReadyMixinSerializer
):
    # Override is_ready field to be read-only and default to True
    is_ready = serializers.BooleanField(read_only=True, default=True)

    class Meta:
        model = ControllerCategory


class ControllerCategoryListReadOnlySerializer(ReadOnlySerializer, ControllerCategorySerializer):
    pin_init_cfg = None  # Hide pin_init_cfg in list view


class ControllerCategoryDetailReadOnlySerializer(ReadOnlySerializer, ControllerCategorySerializer):
    pass


class ControllerCategorySeederSerializer(SeederMixinSerializer, ControllerCategorySerializer):
    pass


class ControllerSerializer(BaseSerializer, NameMixinSerializer, PinOwnerMixinSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=ControllerCategory.objects.all())

    class Meta:
        model = Controller


class ControllerListReadOnlySerializer(ReadOnlySerializer, ControllerSerializer):
    category = MinimalReadOnlySerializer(read_only=True)
    device = DeviceMinimalReadOnlySerializer(source="pin.device", read_only=True)
    pin = PinMinimalReadOnlySerializer(read_only=True)


class ControllerDetailReadOnlySerializer(ControllerListReadOnlySerializer):
    device = DeviceDetailReadOnlySerializer(source="pin.device", read_only=True)
