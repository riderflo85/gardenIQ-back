from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.relations import ManyRelatedField

from gardeniq.users.serializers.groups import GroupSerializer

User = get_user_model()


class GroupSerializerTestCase(TestCase):
    """Test cases for GroupSerializer"""

    def setUp(self):
        """Set up test data"""
        self.content_type = ContentType.objects.get_for_model(User)

        # Create test permissions
        self.permission1 = Permission.objects.create(
            codename='test_group_permission1',
            name='Can test group permission 1',
            content_type=self.content_type
        )
        self.permission2 = Permission.objects.create(
            codename='test_group_permission2',
            name='Can test group permission 2',
            content_type=self.content_type
        )

        # Create test group
        self.group = Group.objects.create(name='Test Group')
        self.group.permissions.add(self.permission1)

    def test_group_serializer_representation(self):
        """Test group serializer representation"""
        serializer = GroupSerializer(instance=self.group)
        data = serializer.data

        self.assertEqual(data['id'], self.group.id)
        self.assertEqual(data['name'], self.group.name)
        self.assertIn('permissions', data)
        self.assertEqual(len(data['permissions']), 1)
        self.assertEqual(data['permissions'][0]['id'], self.permission1.id)

    def test_group_serializer_with_multiple_permissions(self):
        """Test group serializer with multiple permissions"""
        self.group.permissions.add(self.permission2)

        serializer = GroupSerializer(instance=self.group)
        data = serializer.data

        self.assertEqual(len(data['permissions']), 2)
        permission_codenames = [p['codename'] for p in data['permissions']]
        self.assertIn('test_group_permission1', permission_codenames)
        self.assertIn('test_group_permission2', permission_codenames)

    def test_group_serializer_with_no_permissions(self):
        """Test group serializer with no permissions"""
        empty_group = Group.objects.create(name='Empty Group')

        serializer = GroupSerializer(instance=empty_group)
        data = serializer.data

        self.assertEqual(data['name'], 'Empty Group')
        self.assertEqual(len(data['permissions']), 0)

    def test_group_serializer_permissions_readonly(self):
        """Test that permissions field is read-only"""
        serializer = GroupSerializer(instance=self.group)

        self.assertTrue(serializer.fields['permissions'].read_only)

    def test_group_serializer_permission_ids_writeonly(self):
        """Test that permission_ids field is write-only"""
        serializer = GroupSerializer(instance=self.group)

        self.assertTrue(serializer.fields['permission_ids'].write_only)
        # permission_ids should not appear in serialized data
        data = serializer.data
        self.assertNotIn('permission_ids', data)

    def test_group_serializer_id_readonly(self):
        """Test that id field is read-only"""
        serializer = GroupSerializer(instance=self.group)

        self.assertTrue(serializer.fields['id'].read_only)

    def test_group_serializer_cannot_create(self):
        """Test that group serializer cannot create objects"""
        data = {
            'name': 'New Group',
            'permission_ids': [self.permission1.id]
        }
        serializer = GroupSerializer(data=data)

        with self.assertRaises(NotImplementedError) as context:
            if serializer.is_valid():
                serializer.save()

        self.assertIn('does not support creation', str(context.exception))

    def test_group_serializer_cannot_update(self):
        """Test that group serializer cannot update objects"""
        data = {
            'name': 'Updated Group',
            'permission_ids': [self.permission2.id]
        }
        serializer = GroupSerializer(instance=self.group, data=data, partial=True)

        with self.assertRaises(NotImplementedError) as context:
            if serializer.is_valid():
                serializer.save()

        self.assertIn('does not support update', str(context.exception))

    def test_group_serializer_many(self):
        """Test group serializer with many=True"""
        group2 = Group.objects.create(name='Test Group 2')
        group2.permissions.add(self.permission2)

        groups = Group.objects.filter(id__in=[self.group.id, group2.id])
        serializer = GroupSerializer(groups, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        group_names = [g['name'] for g in data]
        self.assertIn('Test Group', group_names)
        self.assertIn('Test Group 2', group_names)

    def test_group_serializer_permissions_detail(self):
        """Test that permissions are serialized with detail"""
        serializer = GroupSerializer(instance=self.group)
        data = serializer.data

        permission_data = data['permissions'][0]
        self.assertIn('id', permission_data)
        self.assertIn('name', permission_data)
        self.assertIn('codename', permission_data)
        self.assertIn('content_type', permission_data)

    def test_group_serializer_name_field(self):
        """Test that name field is writable"""
        serializer = GroupSerializer(instance=self.group)

        self.assertFalse(serializer.fields['name'].read_only)

    def test_group_serializer_permission_ids_queryset(self):
        """Test that permission_ids field has correct queryset"""
        serializer = GroupSerializer(instance=self.group)

        permission_ids_field = serializer.fields['permission_ids']
        # Check that queryset contains Permission objects
        # ManyRelatedField wraps the actual field, access via child_relation
        queryset = permission_ids_field.child_relation.queryset
        self.assertTrue(queryset.model == Permission)

    def test_group_serializer_permission_ids_many(self):
        """Test that permission_ids field accepts many values"""
        serializer = GroupSerializer(instance=self.group)

        permission_ids_field = serializer.fields['permission_ids']
        # Check that it's a ManyRelatedField (which handles many=True)
        self.assertIsInstance(permission_ids_field, ManyRelatedField)

    def test_group_serializer_permission_ids_not_required(self):
        """Test that permission_ids field is not required"""
        serializer = GroupSerializer(instance=self.group)

        permission_ids_field = serializer.fields['permission_ids']
        self.assertFalse(permission_ids_field.required)

    def test_group_serializer_fields_count(self):
        """Test that group serializer has correct number of fields"""
        serializer = GroupSerializer(instance=self.group)

        expected_fields = ['id', 'name', 'permissions', 'permission_ids']
        self.assertEqual(set(serializer.fields.keys()), set(expected_fields))

    def test_group_serializer_empty_queryset(self):
        """Test group serializer with empty queryset"""
        groups = Group.objects.none()
        serializer = GroupSerializer(groups, many=True)
        data = serializer.data

        self.assertEqual(len(data), 0)

    def test_group_serializer_with_null_instance(self):
        """Test group serializer with None instance"""
        serializer = GroupSerializer(instance=None)
        # When instance is None, accessing .data returns an empty ReturnDict
        # which behaves like an empty dict for read-only serializers
        data = serializer.data

        # Verify the data structure is empty or has None/empty values
        self.assertIsInstance(data, dict)

    def test_group_serializer_validation_with_valid_data(self):
        """Test that serializer validates correctly with valid data"""
        data = {
            'name': 'Valid Group',
            'permission_ids': [self.permission1.id, self.permission2.id]
        }
        serializer = GroupSerializer(data=data)

        # Validation should pass even though save will fail
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], 'Valid Group')
        self.assertEqual(len(serializer.validated_data['permissions']), 2)

    def test_group_serializer_validation_with_invalid_permission_ids(self):
        """Test that serializer validates with invalid permission IDs"""
        data = {
            'name': 'Invalid Group',
            'permission_ids': [99999]  # Non-existent permission ID
        }
        serializer = GroupSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('permission_ids', serializer.errors)

    def test_group_serializer_source_mapping(self):
        """Test that permission_ids correctly maps to permissions"""
        data = {
            'name': 'Source Test Group',
            'permission_ids': [self.permission1.id]
        }
        serializer = GroupSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        # Check that permission_ids is mapped to 'permissions' in validated_data
        self.assertIn('permissions', serializer.validated_data)
        self.assertEqual(len(serializer.validated_data['permissions']), 1)
        self.assertEqual(
            serializer.validated_data['permissions'][0].id,
            self.permission1.id
        )
