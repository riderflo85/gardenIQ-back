from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

import pytest

from gardeniq.base.utils.tests import ViewSetTestMixin
from gardeniq.users.serializers.permissions import PermissionReadOnlySerializer


@pytest.mark.django_db
class TestPermissionReadOnlySerializer(ViewSetTestMixin):
    """Test cases for PermissionReadOnlySerializer"""

    def test_permission_serializer_representation(self, test_permission):
        """Test permission serializer representation"""
        # GIVEN: A permission instance
        permission = test_permission

        # WHEN: Serializing the permission
        serializer = PermissionReadOnlySerializer(instance=permission)
        data = serializer.data

        # THEN: All fields are correctly represented
        assert data["id"] == permission.id
        assert data["name"] == permission.name
        assert data["codename"] == permission.codename
        assert "content_type" in data

    def test_permission_serializer_all_fields_readonly(self, test_permission):
        """Test that all fields in permission serializer are read-only"""
        # GIVEN: A permission instance
        permission = test_permission

        # WHEN: Creating a serializer with the permission
        serializer = PermissionReadOnlySerializer(instance=permission)

        # THEN: All fields are read-only
        assert serializer.fields["id"].read_only is True
        assert serializer.fields["name"].read_only is True
        assert serializer.fields["codename"].read_only is True
        assert serializer.fields["content_type"].read_only is True

    def test_permission_serializer_cannot_create(self, user_content_type):
        """Test that permission serializer cannot create objects"""
        # GIVEN: Data for creating a new permission
        data = {"name": "New Permission", "codename": "new_permission", "content_type": user_content_type.id}

        # WHEN: Attempting to create a permission using the serializer
        serializer = PermissionReadOnlySerializer(data=data)

        # THEN: NotImplementedError is raised
        with pytest.raises(NotImplementedError) as exc_info:
            if serializer.is_valid():
                serializer.save()

        assert "cannot save objects" in str(exc_info.value)

    def test_permission_serializer_cannot_update(self, test_permission):
        """Test that permission serializer cannot update objects"""
        # GIVEN: A permission instance and update data
        permission = test_permission
        data = {"name": "Updated Permission"}

        # WHEN: Attempting to update the permission using the serializer
        serializer = PermissionReadOnlySerializer(instance=permission, data=data, partial=True)

        # THEN: NotImplementedError is raised
        with pytest.raises(NotImplementedError) as exc_info:
            if serializer.is_valid():
                serializer.save()

        assert "cannot save objects" in str(exc_info.value)

    def test_permission_serializer_many(self, test_permission, test_permission_2):
        """Test permission serializer with many=True"""
        # GIVEN: Multiple permissions
        permission1 = test_permission
        permission2 = test_permission_2

        # WHEN: Serializing multiple permissions with many=True
        permissions = Permission.objects.filter(id__in=[permission1.id, permission2.id])
        serializer = PermissionReadOnlySerializer(permissions, many=True)
        data = serializer.data

        # THEN: All permissions are correctly serialized
        assert len(data) == 2
        codenames = [p["codename"] for p in data]
        assert permission1.codename in codenames
        assert permission2.codename in codenames

    def test_permission_serializer_content_type_string(self, test_permission):
        """Test that content_type is displayed as string"""
        # GIVEN: A permission instance
        permission = test_permission

        # WHEN: Serializing the permission
        serializer = PermissionReadOnlySerializer(instance=permission)
        data = serializer.data

        # THEN: content_type is a string
        assert isinstance(data["content_type"], str)

    def test_permission_serializer_with_different_content_types(self, user_content_type):
        """Test permission serializer with different content types"""
        # GIVEN: A permission with Group content type
        from django.contrib.contenttypes.models import ContentType

        group_content_type = ContentType.objects.get_for_model(Group)
        group_permission = Permission.objects.create(
            codename="test_group_permission", name="Can test group permission", content_type=group_content_type
        )

        # WHEN: Serializing the group permission
        serializer = PermissionReadOnlySerializer(instance=group_permission)
        data = serializer.data

        # THEN: Permission data is correct and content_type mentions 'group'
        assert data["codename"] == "test_group_permission"
        assert "group" in data["content_type"].lower()

    def test_permission_serializer_empty_queryset(self):
        """Test permission serializer with empty queryset"""
        # GIVEN: An empty permission queryset
        permissions = Permission.objects.none()

        # WHEN: Serializing the empty queryset
        serializer = PermissionReadOnlySerializer(permissions, many=True)
        data = serializer.data

        # THEN: Empty list is returned
        assert len(data) == 0

    def test_permission_serializer_fields_count(self, test_permission):
        """Test that permission serializer has correct number of fields"""
        # GIVEN: A permission instance
        permission = test_permission

        # WHEN: Creating a serializer with the permission
        serializer = PermissionReadOnlySerializer(instance=permission)

        # THEN: Only expected fields are present
        expected_fields = ["id", "name", "codename", "content_type"]
        assert set(serializer.fields.keys()) == set(expected_fields)

    def test_permission_serializer_with_null_instance(self):
        """Test permission serializer with None instance"""
        # GIVEN: A None instance
        # WHEN: Creating a serializer with None
        serializer = PermissionReadOnlySerializer(instance=None)
        data = serializer.data

        # THEN: Data is an empty dict-like structure
        assert isinstance(data, dict)
