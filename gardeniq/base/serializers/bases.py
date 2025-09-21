from typing import Dict

from django.db.models import Model

from rest_framework import serializers

from .mixins import PKMixinSerializer


class BaseSerializer(PKMixinSerializer):
    class Meta:
        model: type[Model]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert hasattr(self.Meta, "model"), (
            "Error missing `model` attribut to `Meta` class for %s"
            % self.__class__.__name__
        )

    def create(self, validated_data: Dict):
        obj = self.Meta.model.objects.create(**validated_data)
        return obj

    def update(self, instance, validated_data: Dict):
        for key, value in validated_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.save()
        return instance


class ReadOnlySerializer(serializers.Serializer):
    def get_fields(self):
        """
        Override the get_fields method to make all fields read_only.
        """
        fields = super().get_fields()
        for field in fields:
            fields[field].read_only = True
        return fields

    def create(self, validated_data):
        """
        Raises NotImplementedError because this read-only serializer does not create objects.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} is read-only and cannot create objects."
        )

    def update(self, instance, validated_data):
        """
        Raises NotImplementedError because this read-only serializer does not update objects.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} is read-only and cannot update objects."
        )
