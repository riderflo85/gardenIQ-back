from django.contrib.auth.models import Permission

from rest_framework import serializers

from .permissions import PermissionSerializer


class GroupSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), source="permissions", write_only=True, required=False
    )

    def create(self, validated_data):
        """
        Raises NotImplementedError because this serializer does not support creation.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support creation.")

    def update(self, instance, validated_data):
        """
        Raises NotImplementedError because this serializer does not support update.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support update.")
