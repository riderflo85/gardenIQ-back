from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from gardeniq.users.serializers.users import UserSerializer, UserReadOnlySerializer

User = get_user_model()


class UserSerializerTestCase(TestCase):
    """Test cases for UserSerializer"""

    def setUp(self):
        """Set up test data"""
        self.content_type = ContentType.objects.get_for_model(User)

        # Create test permissions
        self.permission1 = Permission.objects.create(
            codename='test_permission1',
            name='Test Permission 1',
            content_type=self.content_type
        )
        self.permission2 = Permission.objects.create(
            codename='test_permission2',
            name='Test Permission 2',
            content_type=self.content_type
        )

        # Create test groups
        self.group1 = Group.objects.create(name='Test Group 1')
        self.group1.permissions.add(self.permission1)

        self.group2 = Group.objects.create(name='Test Group 2')
        self.group2.permissions.add(self.permission2)

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user.groups.add(self.group1)
        self.user.user_permissions.add(self.permission1)

    def test_create_user_with_required_fields(self):
        """Test creating a user with required fields"""
        data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.username, 'newuser')
        self.assertTrue(user.check_password('newpass123'))

    def test_create_user_with_all_fields(self):
        """Test creating a user with all fields"""
        data = {
            'username': 'fulluser',
            'password': 'fullpass123',
            'email': 'fulluser@example.com',
            'first_name': 'Full',
            'last_name': 'User',
            'group_ids': [self.group1.id, self.group2.id],
            'permission_ids': [self.permission1.id, self.permission2.id]
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.username, 'fulluser')
        self.assertEqual(user.email, 'fulluser@example.com')
        self.assertEqual(user.first_name, 'Full')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('fullpass123'))
        self.assertEqual(user.groups.count(), 2)
        self.assertIn(self.group1, user.groups.all())
        self.assertIn(self.group2, user.groups.all())
        self.assertEqual(user.user_permissions.count(), 2)

    def test_create_user_without_password_fails(self):
        """Test that creating a user without password fails"""
        data = {
            'username': 'nopassuser'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_create_user_without_username_fails(self):
        """Test that creating a user without username fails"""
        data = {
            'password': 'testpass123'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_create_user_with_short_password_fails(self):
        """Test that creating a user with short password fails"""
        data = {
            'username': 'shortpass',
            'password': 'short'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_create_user_with_blank_username_fails(self):
        """Test that creating a user with blank username fails"""
        data = {
            'username': '',
            'password': 'testpass123'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_create_user_with_duplicate_username_fails(self):
        """Test that creating a user with duplicate username fails"""
        data = {
            'username': 'testuser',  # Already exists
            'password': 'testpass123'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_create_user_with_duplicate_email_fails(self):
        """Test that creating a user with duplicate email fails"""
        data = {
            'username': 'newuser',
            'email': 'testuser@example.com',  # Already exists
            'password': 'testpass123'
        }
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_create_user_with_empty_email(self):
        """Test that creating a user with empty email is allowed"""
        data = {
            'username': 'noemail',
            'password': 'testpass123',
            'email': ''
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, '')

    def test_update_user_basic_fields(self):
        """Test updating user basic fields"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')
        self.assertEqual(user.email, 'updated@example.com')

    def test_update_user_password(self):
        """Test updating user password"""
        old_password = self.user.password
        data = {
            'password': 'newpassword123'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertNotEqual(user.password, old_password)
        self.assertTrue(user.check_password('newpassword123'))

    def test_update_user_username(self):
        """Test updating user username"""
        data = {
            'username': 'updatedusername'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.username, 'updatedusername')

    def test_update_user_with_duplicate_username_fails(self):
        """Test that updating user with duplicate username fails"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        data = {
            'username': 'otheruser'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_update_user_with_duplicate_email_fails(self):
        """Test that updating user with duplicate email fails"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        data = {
            'email': 'other@example.com'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_update_user_with_same_username_succeeds(self):
        """Test that updating user with same username succeeds"""
        data = {
            'username': 'testuser',
            'first_name': 'Updated'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_user_with_same_email_succeeds(self):
        """Test that updating user with same email succeeds"""
        data = {
            'email': 'testuser@example.com',
            'first_name': 'Updated'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_update_user_groups(self):
        """Test updating user groups"""
        data = {
            'group_ids': [self.group2.id]
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.groups.count(), 1)
        self.assertIn(self.group2, user.groups.all())
        self.assertNotIn(self.group1, user.groups.all())

    def test_update_user_permissions(self):
        """Test updating user permissions"""
        data = {
            'permission_ids': [self.permission2.id]
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.user_permissions.count(), 1)
        self.assertIn(self.permission2, user.user_permissions.all())

    def test_update_without_password_required(self):
        """Test that password is not required for update"""
        data = {
            'first_name': 'Updated'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_fields_readonly(self):
        """Test that certain fields are read-only"""
        serializer = UserSerializer(instance=self.user)

        self.assertTrue(serializer.fields['is_staff'].read_only)
        self.assertTrue(serializer.fields['is_active'].read_only)
        self.assertTrue(serializer.fields['last_login'].read_only)
        self.assertTrue(serializer.fields['date_joined'].read_only)
        self.assertTrue(serializer.fields['password'].write_only)

    def test_serializer_representation(self):
        """Test serializer representation"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data

        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['first_name'], self.user.first_name)
        self.assertEqual(data['last_name'], self.user.last_name)
        self.assertNotIn('password', data)  # write_only field

    def test_partial_update(self):
        """Test partial update of user"""
        data = {
            'first_name': 'PartialUpdate'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        # Only first_name should change
        self.assertEqual(user.first_name, 'PartialUpdate')
        self.assertEqual(user.username, 'testuser')  # Unchanged
        self.assertEqual(user.email, 'testuser@example.com')  # Unchanged


class UserReadOnlySerializerTestCase(TestCase):
    """Test cases for UserReadOnlySerializer"""

    def setUp(self):
        """Set up test data"""
        self.content_type = ContentType.objects.get_for_model(User)

        # Create test permissions
        self.permission1 = Permission.objects.create(
            codename='test_ro_permission1',
            name='Test RO Permission 1',
            content_type=self.content_type
        )

        # Create test groups
        self.group1 = Group.objects.create(name='Test RO Group 1')
        self.group1.permissions.add(self.permission1)

        # Create test user
        self.user = User.objects.create_user(
            username='readonly_user',
            email='readonly@example.com',
            password='testpass123',
            first_name='ReadOnly',
            last_name='User'
        )
        self.user.groups.add(self.group1)
        self.user.user_permissions.add(self.permission1)

    def test_readonly_serializer_representation(self):
        """Test that read-only serializer includes groups and permissions"""
        serializer = UserReadOnlySerializer(instance=self.user)
        data = serializer.data

        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)

        # Check groups are serialized
        self.assertIn('groups', data)
        self.assertEqual(len(data['groups']), 1)
        self.assertEqual(data['groups'][0]['id'], self.group1.id)
        self.assertEqual(data['groups'][0]['name'], self.group1.name)

        # Check permissions are serialized
        self.assertIn('user_permissions', data)
        self.assertEqual(len(data['user_permissions']), 1)
        self.assertEqual(data['user_permissions'][0]['id'], self.permission1.id)

    def test_readonly_serializer_all_fields_readonly(self):
        """Test that all fields in read-only serializer are read-only"""
        serializer = UserReadOnlySerializer(instance=self.user)

        for field_name, field in serializer.fields.items():
            self.assertTrue(
                field.read_only,
                f"Field '{field_name}' should be read-only"
            )

    def test_readonly_serializer_cannot_create(self):
        """Test that read-only serializer cannot create objects"""
        data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        serializer = UserReadOnlySerializer(data=data)

        with self.assertRaises(NotImplementedError):
            serializer.save()

    def test_readonly_serializer_with_multiple_groups(self):
        """Test read-only serializer with multiple groups"""
        group2 = Group.objects.create(name='Test RO Group 2')
        self.user.groups.add(group2)

        serializer = UserReadOnlySerializer(instance=self.user)
        data = serializer.data

        self.assertEqual(len(data['groups']), 2)
        group_names = [g['name'] for g in data['groups']]
        self.assertIn('Test RO Group 1', group_names)
        self.assertIn('Test RO Group 2', group_names)

    def test_readonly_serializer_with_multiple_permissions(self):
        """Test read-only serializer with multiple permissions"""
        permission2 = Permission.objects.create(
            codename='test_ro_permission2',
            name='Test RO Permission 2',
            content_type=self.content_type
        )
        self.user.user_permissions.add(permission2)

        serializer = UserReadOnlySerializer(instance=self.user)
        data = serializer.data

        self.assertEqual(len(data['user_permissions']), 2)
        permission_codenames = [p['codename'] for p in data['user_permissions']]
        self.assertIn('test_ro_permission1', permission_codenames)
        self.assertIn('test_ro_permission2', permission_codenames)

    def test_readonly_serializer_groups_include_permissions(self):
        """Test that groups in read-only serializer include their permissions"""
        serializer = UserReadOnlySerializer(instance=self.user)
        data = serializer.data

        group_data = data['groups'][0]
        self.assertIn('permissions', group_data)
        self.assertEqual(len(group_data['permissions']), 1)
        self.assertEqual(group_data['permissions'][0]['id'], self.permission1.id)

    def test_readonly_serializer_with_no_groups_or_permissions(self):
        """Test read-only serializer with user having no groups or permissions"""
        user_no_perms = User.objects.create_user(
            username='nopermsuser',
            password='testpass123'
        )

        serializer = UserReadOnlySerializer(instance=user_no_perms)
        data = serializer.data

        self.assertEqual(len(data['groups']), 0)
        self.assertEqual(len(data['user_permissions']), 0)

    def test_readonly_serializer_many(self):
        """Test read-only serializer with many=True"""
        user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )

        users = User.objects.filter(id__in=[self.user.id, user2.id])
        serializer = UserReadOnlySerializer(users, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        usernames = [u['username'] for u in data]
        self.assertIn('readonly_user', usernames)
        self.assertIn('user2', usernames)
