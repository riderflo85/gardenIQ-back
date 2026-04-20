from django.contrib.auth.models import Permission

from rest_framework import serializers

from gardeniq.base.serializers import ReadOnlySerializer

from .permissions import PermissionReadOnlySerializer


class GroupReadOnlySerializer(ReadOnlySerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    permissions = PermissionReadOnlySerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), source="permissions", write_only=True, required=False
    )
