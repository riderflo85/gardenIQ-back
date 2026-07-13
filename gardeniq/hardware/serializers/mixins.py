from rest_framework import serializers


class PinInitConfigMixinSerializer(serializers.Serializer):
    # TODO: Faire la validation avec JSONSchema pour vérifier que le JSON est bien formé et correspond
    # à la structure attendue
    pin_init_cfg = serializers.JSONField()
