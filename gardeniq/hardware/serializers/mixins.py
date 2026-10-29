from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

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
            raise serializers.ValidationError(e.message_dict)
        return value
