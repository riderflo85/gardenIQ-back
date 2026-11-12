from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from gardeniq.hardware.models import Pin
from gardeniq.hardware.models.mixins import PinOwnerMixin
from gardeniq.hardware.validations import jsonschema_validation


class PinInitConfigMixinSerializer(serializers.Serializer):

    pin_init_cfg = serializers.JSONField()

    def validate_pin_init_cfg(self, value: dict) -> dict:
        """
        Validate the pin_init_cfg JSON field against the PIN_INIT_CONFIG_JSON_SCHEMA defined in settings.

        Args:
            value (dict): The pin_init_cfg JSON data to validate.
        """
        try:
            jsonschema_validation(value, settings.PIN_INIT_CONFIG_JSON_SCHEMA, "pin_init_cfg")
        except DjangoValidationError as e:
            # Convert Django ValidationError to DRF ValidationError.
            raise serializers.ValidationError(e.messages)
        return value


class PinOwnerMixinSerializer(serializers.Serializer):

    pin = serializers.PrimaryKeyRelatedField(queryset=Pin.objects.all())

    def validate_pin(self, value: Pin) -> Pin:
        """
        Refuse a pin already used by a sensor or a controller other than the instance being updated.

        Args:
            value (Pin): The pin to wire the object to.
        """
        for owner in PinOwnerMixin.PIN_OWNERS:
            current = getattr(value, owner, None)
            if current is not None and current != self.instance:
                raise serializers.ValidationError([f"Pin {value.pin_number} is already used by a {owner}."])
        return value
