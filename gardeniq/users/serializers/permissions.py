from rest_framework import serializers

class PermissionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    codename = serializers.CharField(read_only=True)
    content_type = serializers.StringRelatedField(read_only=True)

    def create(self, validated_data):
        """
        Raises NotImplementedError because this serializer does not support creation.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support creation."
        )

    def update(self, instance, validated_data):
        """
        Raises NotImplementedError because this serializer does not support update.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support update."
        )
