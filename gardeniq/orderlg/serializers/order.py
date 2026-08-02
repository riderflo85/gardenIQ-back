from rest_framework import serializers

from gardeniq.base.serializers import AutocompleteSlugMixinSerializer
from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import DescriptionMixinSerializer
from gardeniq.base.serializers import EnabledMixinSerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SeederIsReadyMixinSerializer
from gardeniq.base.serializers import SeederMixinSerializer
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
    SeederIsReadyMixinSerializer,
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
    # Override is_ready field to be read-only and default to True
    is_ready = serializers.BooleanField(read_only=True, default=True)

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

        # `is_ready` can be False if the user updates an Order that was created by the Seeder.
        if attrs.get("is_ready") is False:
            attrs["is_ready"] = True  # Override is_ready to True if False is provided

        return attrs


class OrderListReadOnlySerializer(
    ReadOnlySerializer,
    PKMixinSerializer,
    NameMixinSerializer,
    SimpleSlugMixinSerializer,
    EnabledMixinSerializer,
    SeederIsReadyMixinSerializer,
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


class OrderSeederSerializer(SeederMixinSerializer, OrderSerializer):
    is_ready = serializers.BooleanField(default=True)

    def validate(self, attrs):
        # Bypass the action_type, sensor, and controller validation in OrderSerializer.
        attrs = AutocompleteSlugMixinSerializer.validate(self, attrs)

        seed_id = attrs.get("seed_id", getattr(self.instance, "seed_id", None))
        is_ready = attrs.get("is_ready", getattr(self.instance, "is_ready", None))
        controller = attrs.get("controller", getattr(self.instance, "controller", None))
        sensor = attrs.get("sensor", getattr(self.instance, "sensor", None))

        if seed_id is not None and seed_id > 0 and is_ready is False and controller is None and sensor is None:
            return attrs
        else:
            raise serializers.ValidationError(
                "Invalid constraint: "
                "if seed_id is set and greater than 0, is_ready must be False, "
                "and both controller and sensor must be None."
            )
