from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

from rest_framework.relations import ManyRelatedField

import pytest

from gardeniq.base.utils.tests import ViewSetTestMixin
from gardeniq.users.serializers import GroupReadOnlySerializer


@pytest.mark.django_db
class TestGroupSerializer(ViewSetTestMixin):
    """Test cases for GroupReadOnlySerializer"""

    def test_group_serializer_representation(self, test_group, test_permission):
        """Test group serializer representation"""
        # GIVEN: A group with a permission
        group = test_group
        permission = test_permission

        # WHEN: Serializing the group
        serializer = GroupReadOnlySerializer(instance=group)
        data = serializer.data

        # THEN: All fields are correctly represented
        assert data["id"] == group.id
        assert data["name"] == group.name
        assert "permissions" in data
        assert len(data["permissions"]) == 1
        assert data["permissions"][0]["id"] == permission.id

    def test_group_serializer_with_multiple_permissions(self, test_group, test_permission, test_permission_2):
        """Test group serializer with multiple permissions"""
        # GIVEN: A group with multiple permissions
        group = test_group
        permission1 = test_permission
        permission2 = test_permission_2
        group.permissions.add(permission2)

        # WHEN: Serializing the group
        serializer = GroupReadOnlySerializer(instance=group)
        data = serializer.data

        # THEN: All permissions are present
        assert len(data["permissions"]) == 2
        permission_codenames = [p["codename"] for p in data["permissions"]]
        assert permission1.codename in permission_codenames
        assert permission2.codename in permission_codenames

    def test_group_serializer_with_no_permissions(self):
        """Test group serializer with no permissions"""
        # GIVEN: A group with no permissions
        empty_group = Group.objects.create(name="Empty Group")

        # WHEN: Serializing the group
        serializer = GroupReadOnlySerializer(instance=empty_group)
        data = serializer.data

        # THEN: Group has no permissions
        assert data["name"] == "Empty Group"
        assert len(data["permissions"]) == 0

    def test_group_serializer_permissions_readonly(self, test_group):
        """Test that permissions field is read-only"""
        # GIVEN: A group instance
        group = test_group

        # WHEN: Creating a serializer
        serializer = GroupReadOnlySerializer(instance=group)

        # THEN: permissions field is read-only
        assert serializer.fields["permissions"].read_only is True

    def test_group_serializer_permission_ids_writeonly(self, test_group):
        """Test that permission_ids field is write-only"""
        # GIVEN: A group instance
        group = test_group

        # WHEN: Creating a serializer and accessing data
        serializer = GroupReadOnlySerializer(instance=group)
        data = serializer.data

        # THEN: permission_ids is write-only and not in serialized data
        assert serializer.fields["permission_ids"].write_only is True
        assert "permission_ids" not in data

    def test_group_serializer_id_readonly(self, test_group):
        """Test that id field is read-only"""
        # GIVEN: A group instance
        group = test_group

        # WHEN: Creating a serializer
        serializer = GroupReadOnlySerializer(instance=group)

        # THEN: id field is read-only
        assert serializer.fields["id"].read_only is True

    def test_group_serializer_cannot_create(self, test_permission):
        """Test that group serializer cannot create objects"""
        # GIVEN: Data for creating a new group
        permission = test_permission
        data = {"name": "New Group", "permission_ids": [permission.id]}

        # WHEN: Attempting to create a group using the serializer
        serializer = GroupReadOnlySerializer(data=data)

        # THEN: NotImplementedError is raised
        with pytest.raises(NotImplementedError) as exc_info:
            if serializer.is_valid():
                serializer.save()

        assert "cannot save objects" in str(exc_info.value)

    def test_group_serializer_cannot_update(self, test_group, test_permission_2):
        """Test that group serializer cannot update objects"""
        # GIVEN: A group instance and update data
        group = test_group
        permission2 = test_permission_2
        data = {"name": "Updated Group", "permission_ids": [permission2.id]}

        # WHEN: Attempting to update the group using the serializer
        serializer = GroupReadOnlySerializer(instance=group, data=data, partial=True)

        # THEN: NotImplementedError is raised
        with pytest.raises(NotImplementedError) as exc_info:
            if serializer.is_valid():
                serializer.save()

        assert "cannot save objects" in str(exc_info.value)

    def test_group_serializer_many(self, test_group, test_group_2):
        """Test group serializer with many=True"""
        # GIVEN: Multiple groups
        group1 = test_group
        group2 = test_group_2

        # WHEN: Serializing multiple groups with many=True
        groups = Group.objects.filter(id__in=[group1.id, group2.id])
        serializer = GroupReadOnlySerializer(groups, many=True)
        data = serializer.data

        # THEN: All groups are correctly serialized
        assert len(data) == 2
        group_names = [g["name"] for g in data]
        assert group1.name in group_names
        assert group2.name in group_names

    def test_group_serializer_permissions_detail(self, test_group):
        """Test that permissions are serialized with detail"""
        # GIVEN: A group with permissions
        group = test_group

        # WHEN: Serializing the group
        serializer = GroupReadOnlySerializer(instance=group)
        data = serializer.data

        # THEN: Permission details are included
        permission_data = data["permissions"][0]
        assert "id" in permission_data
        assert "name" in permission_data
        assert "codename" in permission_data
        assert "content_type" in permission_data

    def test_group_serializer_name_field(self, test_group):
        """Test that name field is read-only"""
        # GIVEN: A group instance
        group = test_group

        # WHEN: Creating a serializer
        serializer = GroupReadOnlySerializer(instance=group)

        # THEN: name field is read-only
        assert serializer.fields["name"].read_only is True

    def test_group_serializer_permission_ids_queryset(self, test_group):
        """Test that permission_ids field has correct queryset"""
        # GIVEN: A group instance
        group = test_group

        # WHEN: Creating a serializer and checking permission_ids field
        serializer = GroupReadOnlySerializer(instance=group)
        permission_ids_field = serializer.fields["permission_ids"]
        queryset = permission_ids_field.child_relation.queryset

        # THEN: queryset contains Permission objects
        assert queryset.model == Permission

    def test_group_serializer_permission_ids_many(self, test_group):
        """Test that permission_ids field accepts many values"""
        # GIVEN: A group instance
        group = test_group

        # WHEN: Creating a serializer and checking permission_ids field
        serializer = GroupReadOnlySerializer(instance=group)
        permission_ids_field = serializer.fields["permission_ids"]

        # THEN: Field is a ManyRelatedField
        assert isinstance(permission_ids_field, ManyRelatedField)

    def test_group_serializer_permission_ids_not_required(self, test_group):
        """Test that permission_ids field is not required"""
        # GIVEN: A group instance
        group = test_group

        # WHEN: Creating a serializer and checking permission_ids field
        serializer = GroupReadOnlySerializer(instance=group)
        permission_ids_field = serializer.fields["permission_ids"]

        # THEN: Field is not required
        assert permission_ids_field.required is False

    def test_group_serializer_fields_count(self, test_group):
        """Test that group serializer has correct number of fields"""
        # GIVEN: A group instance
        group = test_group

        # WHEN: Creating a serializer
        serializer = GroupReadOnlySerializer(instance=group)

        # THEN: Only expected fields are present
        expected_fields = ["id", "name", "permissions", "permission_ids"]
        assert set(serializer.fields.keys()) == set(expected_fields)

    def test_group_serializer_empty_queryset(self):
        """Test group serializer with empty queryset"""
        # GIVEN: An empty group queryset
        groups = Group.objects.none()

        # WHEN: Serializing the empty queryset
        serializer = GroupReadOnlySerializer(groups, many=True)
        data = serializer.data

        # THEN: Empty list is returned
        assert len(data) == 0

    def test_group_serializer_with_null_instance(self):
        """Test group serializer with None instance"""
        # GIVEN: A None instance
        # WHEN: Creating a serializer with None
        serializer = GroupReadOnlySerializer(instance=None)
        data = serializer.data

        # THEN: Data is an empty dict-like structure
        assert isinstance(data, dict)

    def test_group_serializer_validation_with_valid_data(self, test_permission, test_permission_2):
        """Test that serializer ignores input data since all fields are read-only"""
        # GIVEN: Valid data with existing permission ids
        permission1 = test_permission
        permission2 = test_permission_2
        data = {"name": "Valid Group", "permission_ids": [permission1.id, permission2.id]}

        # WHEN: Validating the data
        serializer = GroupReadOnlySerializer(data=data)

        # THEN: Validation passes but validated_data is empty since all fields are read-only
        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

    def test_group_serializer_validation_with_invalid_permission_ids(self):
        """Test that invalid permission IDs are ignored since the field is read-only"""
        # GIVEN: Data with non-existent permission ID
        data = {"name": "Invalid Group", "permission_ids": [99999]}

        # WHEN: Validating the data
        serializer = GroupReadOnlySerializer(data=data)

        # THEN: Validation passes since all fields are read-only and input is ignored
        assert serializer.is_valid() is True
        assert serializer.validated_data == {}

    def test_group_serializer_source_mapping(self, test_permission):
        """Test that permission_ids is not mapped to validated_data since fields are read-only"""
        # GIVEN: Data with permission_ids
        permission = test_permission
        data = {"name": "Source Test Group", "permission_ids": [permission.id]}

        # WHEN: Validating the data
        serializer = GroupReadOnlySerializer(data=data)

        # THEN: validated_data is empty since all fields are read-only
        assert serializer.is_valid() is True
        assert serializer.validated_data == {}
