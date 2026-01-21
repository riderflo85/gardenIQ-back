from rest_framework import serializers

from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import DescriptionMixinSerializer
from gardeniq.base.serializers import EnabledMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SimpleSlugMixinSerializer
from gardeniq.orderlg.models import Argument


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
