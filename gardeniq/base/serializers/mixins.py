from django.utils.text import slugify

from rest_framework import serializers


class PKMixinSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)


class NameMixinSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class DescriptionMixinSerializer(serializers.Serializer):
    description = serializers.CharField()


class OptionalDescriptionMixinSerializer(serializers.Serializer):
    description = serializers.CharField(required=False, allow_blank=True)


class SimpleSlugMixinSerializer(serializers.Serializer):
    slug = serializers.SlugField()


class AutocompleteSlugMixinSerializer(serializers.Serializer):
    slug = serializers.SlugField(required=False)

    class Meta:
        prepopulated_slug_with: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert hasattr(self.Meta, "prepopulated_slug_with"), (
            "Error missing `prepopulated_slug_with` attribut to `Meta` class for %s"
            % self.__class__.__name__
        )

    def validate(self, data):
        if not data.get("slug", False) and not self.fields["slug"].read_only:
            data["slug"] = slugify(data[self.Meta.prepopulated_slug_with])
        return super().validate(data)


class EnabledMixinSerializer(serializers.Serializer):
    is_enabled = serializers.BooleanField(default=True)
