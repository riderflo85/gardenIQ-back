from rest_framework import serializers

from gardeniq.base.serializers import AutocompleteSlugMixinSerializer
from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import DescriptionMixinSerializer
from gardeniq.base.serializers import EnabledMixinSerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SimpleSlugMixinSerializer
from gardeniq.base.serializers.mixins import PKMixinSerializer
from gardeniq.orderlg.models import Order


class OrderSerializer(
    BaseSerializer,
    NameMixinSerializer,
    DescriptionMixinSerializer,
    AutocompleteSlugMixinSerializer,
    EnabledMixinSerializer,
):
    action_type = serializers.ChoiceField(choices=Order.ACTIONS_CHOICES)

    class Meta(BaseSerializer.Meta, AutocompleteSlugMixinSerializer.Meta):
        model = Order
        prepopulated_slug_with = "name"


class OrderListReadOnlySerializer(
    ReadOnlySerializer,
    PKMixinSerializer,
    NameMixinSerializer,
    SimpleSlugMixinSerializer,
    EnabledMixinSerializer,
):
    action_type = serializers.CharField(read_only=True)


class OrderDetailReadOnlySerializer(OrderListReadOnlySerializer, DescriptionMixinSerializer):
    pass
