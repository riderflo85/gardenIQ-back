from rest_framework import serializers

from gardeniq.base.serializers import ReadOnlySerializer


class PermissionReadOnlySerializer(ReadOnlySerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    codename = serializers.CharField(read_only=True)
    content_type = serializers.StringRelatedField(read_only=True)
