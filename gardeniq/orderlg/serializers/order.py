from rest_framework import serializers

from gardeniq.base.serializers import AutocompleteSlugMixinSerializer
from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import DescriptionMixinSerializer
from gardeniq.base.serializers import EnabledMixinSerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SimpleSlugMixinSerializer
from gardeniq.base.serializers.mixins import PKMixinSerializer
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.serializers import ControllerListReadOnlySerializer
from gardeniq.hardware.serializers import SensorListReadOnlySerializer
from gardeniq.orderlg.models import Order


class OrderSerializer(
    BaseSerializer,
    NameMixinSerializer,
    DescriptionMixinSerializer,
    AutocompleteSlugMixinSerializer,
    EnabledMixinSerializer,
):
    action_type = serializers.ChoiceField(choices=Order.ACTIONS_CHOICES)
    sensor = serializers.PrimaryKeyRelatedField(
        queryset=Sensor.objects.all(),
        required=False,
        allow_null=True,
    )
    controller = serializers.PrimaryKeyRelatedField(
        queryset=Controller.objects.all(),
        required=False,
        allow_null=True,
    )
    is_toggle_ctrl_value = serializers.BooleanField(required=False)
    ctrl_value = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    class Meta(BaseSerializer.Meta, AutocompleteSlugMixinSerializer.Meta):
        model = Order
        prepopulated_slug_with = "name"

    def validate(self, attrs):
        attrs = super().validate(attrs)

        action_type = attrs.get("action_type", getattr(self.instance, "action_type", None))
        sensor = attrs.get("sensor", getattr(self.instance, "sensor", None))
        controller = attrs.get("controller", getattr(self.instance, "controller", None))

        is_valid_get = action_type == "get" and (sensor is not None or controller is not None)
        is_valid_set = action_type == "set" and (controller is not None and sensor is None)

        if not (is_valid_get or is_valid_set):
            raise serializers.ValidationError(
                "Invalid constraint: "
                "if action_type='get' then sensor or controller must be set; "
                "if action_type='set' then controller must be set and sensor must be empty."
            )

        return attrs


class OrderListReadOnlySerializer(
    ReadOnlySerializer,
    PKMixinSerializer,
    NameMixinSerializer,
    SimpleSlugMixinSerializer,
    EnabledMixinSerializer,
):
    action_type = serializers.CharField(read_only=True)
    sensor = serializers.CharField(read_only=True, source="sensor.name")
    controller = serializers.CharField(read_only=True, source="controller.name")


class OrderDetailReadOnlySerializer(OrderListReadOnlySerializer, DescriptionMixinSerializer):
    sensor = SensorListReadOnlySerializer(read_only=True)
    controller = ControllerListReadOnlySerializer(read_only=True)
    is_toggle_ctrl_value = serializers.BooleanField(read_only=True)
    ctrl_value = serializers.CharField(
        read_only=True,
        allow_blank=True,
        allow_null=True,
    )
