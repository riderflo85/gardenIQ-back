from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from gardeniq.users.serializers.permissions import PermissionSerializer

User = get_user_model()


class PermissionSerializerTestCase(TestCase):
    """Test cases for PermissionSerializer"""

    def setUp(self):
        """Set up test data"""
        self.content_type = ContentType.objects.get_for_model(User)

        # Create test permission
        self.permission = Permission.objects.create(
            codename='test_permission',
            name='Can test permission',
            content_type=self.content_type
        )

    def test_permission_serializer_representation(self):
        """Test permission serializer representation"""
        serializer = PermissionSerializer(instance=self.permission)
        data = serializer.data

        self.assertEqual(data['id'], self.permission.id)
        self.assertEqual(data['name'], self.permission.name)
        self.assertEqual(data['codename'], self.permission.codename)
        self.assertIn('content_type', data)

    def test_permission_serializer_all_fields_readonly(self):
        """Test that all fields in permission serializer are read-only"""
        serializer = PermissionSerializer(instance=self.permission)

        self.assertTrue(serializer.fields['id'].read_only)
        self.assertTrue(serializer.fields['name'].read_only)
        self.assertTrue(serializer.fields['codename'].read_only)
        self.assertTrue(serializer.fields['content_type'].read_only)

    def test_permission_serializer_cannot_create(self):
        """Test that permission serializer cannot create objects"""
        data = {
            'name': 'New Permission',
            'codename': 'new_permission',
            'content_type': self.content_type.id
        }
        serializer = PermissionSerializer(data=data)

        with self.assertRaises(NotImplementedError) as context:
            if serializer.is_valid():
                serializer.save()

        self.assertIn('does not support creation', str(context.exception))

    def test_permission_serializer_cannot_update(self):
        """Test that permission serializer cannot update objects"""
        data = {
            'name': 'Updated Permission'
        }
        serializer = PermissionSerializer(instance=self.permission, data=data, partial=True)

        with self.assertRaises(NotImplementedError) as context:
            if serializer.is_valid():
                serializer.save()

        self.assertIn('does not support update', str(context.exception))

    def test_permission_serializer_many(self):
        """Test permission serializer with many=True"""
        permission2 = Permission.objects.create(
            codename='test_permission2',
            name='Can test permission 2',
            content_type=self.content_type
        )

        permissions = Permission.objects.filter(
            id__in=[self.permission.id, permission2.id]
        )
        serializer = PermissionSerializer(permissions, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        codenames = [p['codename'] for p in data]
        self.assertIn('test_permission', codenames)
        self.assertIn('test_permission2', codenames)

    def test_permission_serializer_content_type_string(self):
        """Test that content_type is displayed as string"""
        serializer = PermissionSerializer(instance=self.permission)
        data = serializer.data

        # StringRelatedField should return the string representation
        self.assertIsInstance(data['content_type'], str)

    def test_permission_serializer_with_different_content_types(self):
        """Test permission serializer with different content types"""
        from django.contrib.auth.models import Group

        group_content_type = ContentType.objects.get_for_model(Group)
        group_permission = Permission.objects.create(
            codename='test_group_permission',
            name='Can test group permission',
            content_type=group_content_type
        )

        serializer = PermissionSerializer(instance=group_permission)
        data = serializer.data

        self.assertEqual(data['codename'], 'test_group_permission')
        self.assertIn('group', data['content_type'].lower())

    def test_permission_serializer_empty_queryset(self):
        """Test permission serializer with empty queryset"""
        permissions = Permission.objects.none()
        serializer = PermissionSerializer(permissions, many=True)
        data = serializer.data

        self.assertEqual(len(data), 0)

    def test_permission_serializer_fields_count(self):
        """Test that permission serializer has correct number of fields"""
        serializer = PermissionSerializer(instance=self.permission)

        expected_fields = ['id', 'name', 'codename', 'content_type']
        self.assertEqual(set(serializer.fields.keys()), set(expected_fields))

    def test_permission_serializer_with_null_instance(self):
        """Test permission serializer with None instance"""
        serializer = PermissionSerializer(instance=None)
        # When instance is None, accessing .data returns an empty ReturnDict
        data = serializer.data

        # Verify the data structure is empty or has None/empty values
        self.assertIsInstance(data, dict)
