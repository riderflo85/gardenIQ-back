from typing import Dict

from rest_framework import serializers

from gardeniq.base.serializers import AutocompleteSlugMixinSerializer
from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import DescriptionMixinSerializer
from gardeniq.base.serializers import EnabledMixinSerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SimpleSlugMixinSerializer
from gardeniq.base.serializers.mixins import PKMixinSerializer
from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import ArgumentSerializer


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


class OrderListReadOnlySerializer(
    ReadOnlySerializer,
    PKMixinSerializer,
    NameMixinSerializer,
    SimpleSlugMixinSerializer,
    EnabledMixinSerializer,
):
    action_type = serializers.CharField(read_only=True)


class OrderDetailReadOnlySerializer(OrderListReadOnlySerializer, DescriptionMixinSerializer):
    arguments = ArgumentSerializer(many=True, read_only=True)
