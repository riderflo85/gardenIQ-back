import re

from rest_framework import serializers

from gardeniq.base.models import Status
from gardeniq.base.serializers import BaseSerializer
from gardeniq.base.serializers import NameMixinSerializer
from gardeniq.base.serializers import OptionalDescriptionMixinSerializer
from gardeniq.base.serializers import ReadOnlySerializer
from gardeniq.base.serializers import SeederIsReadyMixinSerializer
from gardeniq.base.serializers import SeederMixinSerializer

color_regex = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")


class StatusSerializer(
    BaseSerializer,
    NameMixinSerializer,
    OptionalDescriptionMixinSerializer,
):
    tag = serializers.SlugField()
    color = serializers.RegexField(
        color_regex,
        max_length=7,
        min_length=3,
        default=Status.DEFAULT_COLOR,
    )

    class Meta:
        model = Status


class StatusReadOnlySerializer(ReadOnlySerializer, SeederIsReadyMixinSerializer, StatusSerializer):
    """
    Note:
        Using a read-only serializer improves performance,
        as it avoids checks and processing related to data validation and modification.
    Serializer for read-only representation of Status instances.

    Inherits from:
        ReadOnlySerializer: Provides read-only serialization behavior.
        SeederIsReadyMixinSerializer: Adds the `is_ready` field to the serializer.
        StatusSerializer: Base serializer for Status model.

    This serializer is intended for use cases where Status data should be exposed
    in a read-only format, preventing any modifications through the API.
    """

    pass


class StatusSeederSerializer(SeederMixinSerializer, StatusSerializer):
    """
    Serializer for seeding Status instances with additional fields for seeding.

    Inherits from:
        SeederMixinSerializer: Provides fields and behavior for seeding.
        StatusSerializer: Base serializer for Status model.

    This serializer is intended for use cases where Status data should be seeded
    with additional fields, such as `seed_id` and `is_ready`.
    """

    pass
