import pytest

from gardeniq.base.models.status import Status


@pytest.fixture
def status_data():
    """Fixture providing basic data to create a Status."""
    return {
        "name": "In progress",
        "tag": "in-progress",
        "color": "#3498db",
        "description": "Task in progress",
    }


@pytest.fixture
def status_without_description():
    """Fixture providing data without description."""
    return {
        "name": "To do",
        "tag": "todo",
        "color": "#95a5a6",
    }


@pytest.fixture
def status_with_default_color():
    """Fixture providing data without custom color."""
    return {
        "name": "New",
        "tag": "new",
    }


@pytest.mark.django_db
class TestStatusCreation:
    """Tests for Status model creation."""

    def test_create_status_with_all_fields(self, status_data):
        """
        GIVEN: complete data for a Status
        WHEN: creating a Status with all fields
        THEN: the Status is created with correct values
        """
        # GIVEN - data is provided by the status_data fixture

        # WHEN
        status = Status.objects.create(**status_data)

        # THEN
        assert status.pk is not None
        assert status.name == status_data["name"]
        assert status.tag == status_data["tag"]
        assert status.color == status_data["color"]
        assert status.description == status_data["description"]

    def test_create_status_without_description(self, status_without_description):
        """
        GIVEN: data without the description field
        WHEN: creating a Status without description
        THEN: the Status is created with an empty description
        """
        # GIVEN - data is provided by the fixture

        # WHEN
        status = Status.objects.create(**status_without_description)

        # THEN
        assert status.pk is not None
        assert status.name == status_without_description["name"]
        assert status.tag == status_without_description["tag"]
        assert status.description == ""

    def test_create_status_with_default_color(self, status_with_default_color):
        """
        GIVEN: data without the color field
        WHEN: creating a Status without specifying a color
        THEN: the Status is created with the default color
        """
        # GIVEN - data is provided by the fixture

        # WHEN
        status = Status.objects.create(**status_with_default_color)

        # THEN
        assert status.pk is not None
        assert status.color == Status.DEFAULT_COLOR
        assert status.color == "#A2A2A2"


@pytest.mark.django_db
class TestStatusStringRepresentation:
    """Tests for Status model string representation."""

    def test_str_method_returns_correct_format(self, status_data):
        """
        GIVEN: a created Status
        WHEN: calling the __str__ method
        THEN: it returns the format "Status `{name}` : {tag}"
        """
        # GIVEN
        status = Status.objects.create(**status_data)

        # WHEN
        result = str(status)

        # THEN
        expected = f"Status `{status_data['name']}` : {status_data['tag']}"
        assert result == expected


@pytest.mark.django_db
class TestStatusFields:
    """Tests for Status model fields and constraints."""

    def test_name_field_max_length(self):
        """
        GIVEN: a name of 255 characters (maximum length)
        WHEN: creating a Status with this name
        THEN: the Status is created without error
        """
        # GIVEN
        long_name = "A" * 255

        # WHEN
        status = Status.objects.create(
            name=long_name,
            tag="test-long-name",
        )

        # THEN
        assert status.name == long_name
        assert len(status.name) == 255

    def test_color_field_max_length(self):
        """
        GIVEN: a valid hexadecimal color of 7 characters
        WHEN: creating a Status with this color
        THEN: the Status is created with the correct color
        """
        # GIVEN
        hex_color = "#FF5733"

        # WHEN
        status = Status.objects.create(
            name="Test color",
            tag="test-color",
            color=hex_color,
        )

        # THEN
        assert status.color == hex_color
        assert len(status.color) == 7

    def test_tag_is_slug_field(self):
        """
        GIVEN: a valid tag in slug format
        WHEN: creating a Status with this tag
        THEN: the Status is created with the correct tag
        """
        # GIVEN
        slug_tag = "pending-validation"

        # WHEN
        status = Status.objects.create(
            name="Pending validation",
            tag=slug_tag,
        )

        # THEN
        assert status.tag == slug_tag

    def test_description_can_be_blank(self):
        """
        GIVEN: data without description
        WHEN: creating and saving a Status
        THEN: the description field is empty and accepts blank=True
        """
        # GIVEN / WHEN
        status = Status.objects.create(
            name="Test",
            tag="test",
        )

        # THEN
        assert status.description == ""
        # Verify that the field accepts blank
        status.full_clean()  # Should not raise an exception


@pytest.mark.django_db
class TestStatusUpdate:
    """Tests for Status model update operations."""

    def test_update_status_color(self, status_data):
        """
        GIVEN: an existing Status
        WHEN: updating its color
        THEN: the color is modified correctly
        """
        # GIVEN
        status = Status.objects.create(**status_data)
        new_color = "#FF0000"

        # WHEN
        status.color = new_color
        status.save()

        # THEN
        updated_status = Status.objects.get(pk=status.pk)
        assert updated_status.color == new_color

    def test_update_status_description(self, status_data):
        """
        GIVEN: an existing Status with a description
        WHEN: updating its description
        THEN: the description is modified correctly
        """
        # GIVEN
        status = Status.objects.create(**status_data)
        new_description = "Updated new description"

        # WHEN
        status.description = new_description
        status.save()

        # THEN
        updated_status = Status.objects.get(pk=status.pk)
        assert updated_status.description == new_description


@pytest.mark.django_db
class TestStatusDeletion:
    """Tests for deletion of the Status model."""

    def test_delete_status(self, status_data):
        """
        GIVEN: an existing Status
        WHEN: deleting this Status
        THEN: the Status no longer exists in the database
        """
        # GIVEN
        status = Status.objects.create(**status_data)
        status_id = status.pk

        # WHEN
        status.delete()

        # THEN
        assert not Status.objects.filter(pk=status_id).exists()
