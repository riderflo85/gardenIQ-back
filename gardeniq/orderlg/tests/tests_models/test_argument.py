import pytest

from gardeniq.orderlg.models import Argument


@pytest.fixture
def argument_data():
    """Fixture providing basic data to create an Argument."""
    return {
        "description": "Sensor ID to query",
        "slug": "sensor-id",
        "value_type": "int",
        "required": True,
        "is_option": False,
    }


@pytest.fixture
def argument_with_defaults():
    """Fixture providing minimal data relying on defaults."""
    return {
        "description": "Verbose mode",
        "slug": "verbose",
        "value_type": "bool",
    }


@pytest.fixture
def argument_option():
    """Fixture providing data for an option argument."""
    return {
        "description": "Debug mode",
        "slug": "debug",
        "value_type": "none",
        "required": False,
        "is_option": True,
    }


@pytest.mark.django_db
class TestArgumentCreation:
    """Tests for Argument model creation."""

    def test_create_argument_with_all_fields(self, argument_data):
        """
        GIVEN: complete data for an Argument
        WHEN: creating an Argument with all fields
        THEN: the Argument is created with correct values
        """
        # GIVEN - data is provided by the argument_data fixture

        # WHEN
        argument = Argument.objects.create(**argument_data)

        # THEN
        assert argument.pk is not None
        assert argument.description == argument_data["description"]
        assert argument.slug == argument_data["slug"]
        assert argument.value_type == argument_data["value_type"]
        assert argument.required == argument_data["required"]
        assert argument.is_option == argument_data["is_option"]
        assert argument.is_enabled is True  # from ProtectedDisabledMixinModel

    def test_create_argument_with_defaults(self, argument_with_defaults):
        """
        GIVEN: data without optional fields
        WHEN: creating an Argument with minimal data
        THEN: the Argument is created with default values
        """
        # GIVEN - data is provided by the fixture

        # WHEN
        argument = Argument.objects.create(**argument_with_defaults)

        # THEN
        assert argument.pk is not None
        assert argument.description == argument_with_defaults["description"]
        assert argument.slug == argument_with_defaults["slug"]
        assert argument.value_type == argument_with_defaults["value_type"]
        assert argument.required is True  # default value
        assert argument.is_option is False  # default value
        assert argument.is_enabled is True

    def test_create_argument_option(self, argument_option):
        """
        GIVEN: data for an option argument (without value)
        WHEN: creating an Argument with is_option=True
        THEN: the Argument is created as an option
        """
        # GIVEN - data is provided by the fixture

        # WHEN
        argument = Argument.objects.create(**argument_option)

        # THEN
        assert argument.pk is not None
        assert argument.is_option is True
        assert argument.required is False
        assert argument.value_type == "none"

    def test_create_argument_with_each_value_type(self):
        """
        GIVEN: all available value types
        WHEN: creating an Argument for each value type
        THEN: each Argument is created with the correct value_type
        """
        # GIVEN
        value_types = ["int", "float", "str", "bool", "list", "none"]

        for value_type in value_types:
            # WHEN
            argument = Argument.objects.create(
                description=f"Test {value_type}",
                slug=f"test-{value_type}",
                value_type=value_type,
            )

            # THEN
            assert argument.value_type == value_type
            assert argument.pk is not None


@pytest.mark.django_db
class TestArgumentStringRepresentation:
    """Tests for Argument model string representation."""

    def test_str_method_returns_correct_format_when_enabled(self, argument_data):
        """
        GIVEN: a created enabled Argument
        WHEN: calling the __str__ method
        THEN: it returns the format "Argument `{slug}` enabled"
        """
        # GIVEN
        argument = Argument.objects.create(**argument_data)

        # WHEN
        result = str(argument)

        # THEN
        expected = f"Argument `{argument_data['slug']}` enabled"
        assert result == expected

    def test_str_method_returns_correct_format_when_disabled(self, argument_data):
        """
        GIVEN: a created disabled Argument
        WHEN: calling the __str__ method
        THEN: it returns the format "Argument `{slug}` disabled"
        """
        # GIVEN
        argument_data["is_enabled"] = False
        argument = Argument.objects.create(**argument_data)

        # WHEN
        result = str(argument)

        # THEN
        expected = f"Argument `{argument_data['slug']}` disabled"
        assert result == expected


@pytest.mark.django_db
class TestArgumentFields:
    """Tests for Argument model fields and constraints."""

    def test_description_field(self, argument_data):
        """
        GIVEN: a description for an Argument
        WHEN: creating an Argument with this description
        THEN: the Argument is created with the correct description
        """
        # GIVEN
        long_description = "A" * 500

        # WHEN
        argument = Argument.objects.create(
            description=long_description,
            slug="test-long-description",
            value_type="str",
        )

        # THEN
        assert argument.description == long_description

    def test_slug_field(self, argument_data):
        """
        GIVEN: a valid slug
        WHEN: creating an Argument with this slug
        THEN: the Argument is created with the correct slug
        """
        # GIVEN
        slug = "sensor-temperature-external"

        # WHEN
        argument = Argument.objects.create(
            description="External temperature sensor",
            slug=slug,
            value_type="float",
        )

        # THEN
        assert argument.slug == slug

    def test_required_field_default_is_true(self):
        """
        GIVEN: data without specifying required field
        WHEN: creating an Argument
        THEN: the required field defaults to True
        """
        # GIVEN / WHEN
        argument = Argument.objects.create(
            description="Test",
            slug="test",
            value_type="str",
        )

        # THEN
        assert argument.required is True

    def test_is_option_field_default_is_false(self):
        """
        GIVEN: data without specifying is_option field
        WHEN: creating an Argument
        THEN: the is_option field defaults to False
        """
        # GIVEN / WHEN
        argument = Argument.objects.create(
            description="Test",
            slug="test",
            value_type="str",
        )

        # THEN
        assert argument.is_option is False

    def test_is_enabled_field_default_is_true(self):
        """
        GIVEN: data without specifying is_enabled field
        WHEN: creating an Argument
        THEN: the is_enabled field defaults to True
        """
        # GIVEN / WHEN
        argument = Argument.objects.create(
            description="Test",
            slug="test",
            value_type="str",
        )

        # THEN
        assert argument.is_enabled is True


@pytest.mark.django_db
class TestArgumentUpdate:
    """Tests for Argument model update operations."""

    def test_update_argument_description(self, argument_data):
        """
        GIVEN: an existing Argument
        WHEN: updating its description
        THEN: the description is modified correctly
        """
        # GIVEN
        argument = Argument.objects.create(**argument_data)
        new_description = "Updated sensor ID description"

        # WHEN
        argument.description = new_description
        argument.save()

        # THEN
        updated_argument = Argument.objects.get(pk=argument.pk)
        assert updated_argument.description == new_description

    def test_update_argument_value_type(self, argument_data):
        """
        GIVEN: an existing Argument
        WHEN: updating its value_type
        THEN: the value_type is modified correctly
        """
        # GIVEN
        argument = Argument.objects.create(**argument_data)
        new_value_type = "str"

        # WHEN
        argument.value_type = new_value_type
        argument.save()

        # THEN
        updated_argument = Argument.objects.get(pk=argument.pk)
        assert updated_argument.value_type == new_value_type

    def test_update_argument_required_status(self, argument_data):
        """
        GIVEN: an existing required Argument
        WHEN: updating its required status to False
        THEN: the required field is modified correctly
        """
        # GIVEN
        argument = Argument.objects.create(**argument_data)
        assert argument.required is True

        # WHEN
        argument.required = False
        argument.save()

        # THEN
        updated_argument = Argument.objects.get(pk=argument.pk)
        assert updated_argument.required is False

    def test_update_argument_enabled_status(self, argument_data):
        """
        GIVEN: an existing enabled Argument
        WHEN: disabling the Argument
        THEN: the is_enabled field is modified correctly
        """
        # GIVEN
        argument = Argument.objects.create(**argument_data)
        assert argument.is_enabled is True

        # WHEN
        argument.is_enabled = False
        argument.save()

        # THEN
        updated_argument = Argument.objects.get(pk=argument.pk)
        assert updated_argument.is_enabled is False


@pytest.mark.django_db
class TestArgumentDeletion:
    """Tests for deletion of the Argument model."""

    def test_delete_argument(self, argument_data):
        """
        GIVEN: an existing Argument
        WHEN: deleting this Argument
        THEN: the Argument no longer exists in the database
        """
        # GIVEN
        argument = Argument.objects.create(**argument_data)
        argument_id = argument.pk

        # WHEN
        argument.delete()

        # THEN
        assert not Argument.objects.filter(pk=argument_id).exists()

    def test_delete_multiple_arguments(self):
        """
        GIVEN: multiple existing Arguments
        WHEN: deleting all Arguments
        THEN: no Arguments exist in the database
        """
        # GIVEN
        Argument.objects.create(description="Arg 1", slug="arg-1", value_type="int")
        Argument.objects.create(description="Arg 2", slug="arg-2", value_type="str")
        Argument.objects.create(description="Arg 3", slug="arg-3", value_type="bool")
        assert Argument.objects.count() == 3

        # WHEN
        Argument.objects.all().delete()

        # THEN
        assert Argument.objects.count() == 0


@pytest.mark.django_db
class TestArgumentManager:
    """Tests for Argument model custom manager (enabled)."""

    def test_enabled_manager_returns_only_enabled_arguments(self):
        """
        GIVEN: multiple Arguments with different enabled statuses
        WHEN: querying with the enabled manager
        THEN: only enabled Arguments are returned
        """
        # GIVEN
        enabled_arg1 = Argument.objects.create(
            description="Enabled 1",
            slug="enabled-1",
            value_type="int",
            is_enabled=True,
        )
        enabled_arg2 = Argument.objects.create(
            description="Enabled 2",
            slug="enabled-2",
            value_type="str",
            is_enabled=True,
        )
        Argument.objects.create(
            description="Disabled",
            slug="disabled",
            value_type="bool",
            is_enabled=False,
        )

        # WHEN
        enabled_arguments = Argument.enabled.all()

        # THEN
        assert enabled_arguments.count() == 2
        assert enabled_arg1 in enabled_arguments
        assert enabled_arg2 in enabled_arguments
