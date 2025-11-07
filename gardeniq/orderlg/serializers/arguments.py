from typing import Dict

from rest_framework import serializers

from gardeniq.base.serializers import AutocompleteSlugMixinSerializer
from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import DescriptionMixinSerializer
from gardeniq.base.serializers import EnabledMixinSerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SimpleSlugMixinSerializer
from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.models import Order


class ArgumentSerializer(
    BaseSerializer,
    DescriptionMixinSerializer,
    SimpleSlugMixinSerializer,
    EnabledMixinSerializer,
):
    value_type = serializers.ChoiceField(choices=Argument.VALUES_TYPE_CHOICES)
    required = serializers.BooleanField(default=True)
    is_option = serializers.BooleanField(default=False)

    class Meta:
        model = Argument


class ArgumentReadOnlySerializer(ReadOnlySerializer, ArgumentSerializer):
    """
    Note:
        Using a read-only serializer improves performance,
        as it avoids checks and processing related to data validation and modification.
    Serializer for read-only representation of Argument instances.

    Inherits from:
        ReadOnlySerializer: Provides read-only serialization behavior.
        ArgumentSerializer: Base serializer for Argument model.

    This serializer is intended for use cases where Argument data should be exposed
    in a read-only format, preventing any modifications through the API.
    """
    pass


class OrderSerializer(
    BaseSerializer,
    NameMixinSerializer,
    DescriptionMixinSerializer,
    AutocompleteSlugMixinSerializer,
    EnabledMixinSerializer,
):
    action_type = serializers.ChoiceField(choices=Order.ACTIONS_CHOICES)
    arguments = serializers.PrimaryKeyRelatedField(
        queryset=Argument.enabled.all(),
        many=True,
        required=False,
    )

    class Meta(BaseSerializer.Meta, AutocompleteSlugMixinSerializer.Meta):
        model = Order
        prepopulated_slug_with = "name"

    def create(self, validated_data: Dict):
        arguments = validated_data.pop("arguments")
        new_order_obj = super().create(validated_data)
        new_order_obj.arguments.set(arguments)  # pyright: ignore[reportAttributeAccessIssue]
        return new_order_obj

    def update(self, instance, validated_data: Dict):
        arguments = validated_data.pop("arguments")
        instance = super().update(instance, validated_data)
        instance.arguments.set(arguments)
        return instance


class OrderDetailReadOnlySerializer(ReadOnlySerializer, OrderSerializer):
    arguments = ArgumentSerializer(many=True, read_only=True)
