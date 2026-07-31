import pytest

from gardeniq.base.models import Status
from gardeniq.base.serializers import StatusReadOnlySerializer
from gardeniq.base.serializers import StatusSeederSerializer
from gardeniq.base.serializers import StatusSerializer


@pytest.mark.django_db
class TestStatusSerializer:

    def test_valide_serializer(self):
        # GIVEN
        data = {
            "name": "In Progress",
            "description": "Task currently running",
            "tag": "in-progress",
            "color": "#FF5733",
        }
        expected = {
            "name": "In Progress",
            "description": "Task currently running",
            "tag": "in-progress",
            "color": "#FF5733",
        }

        # WHEN
        ser = StatusSerializer(data=data)

        # THEN
        assert ser.is_valid()
        assert ser.data == expected

    def test_valide_serializer_with_default_color(self):
        # GIVEN
        data = {
            "name": "Pending",
            "tag": "pending",
        }
        expected = {
            "name": "Pending",
            "tag": "pending",
            "color": Status.DEFAULT_COLOR,
        }

        # WHEN
        ser = StatusSerializer(data=data)

        # THEN
        assert ser.is_valid()
        assert ser.data == expected

    def test_valide_serializer_with_short_hex_color(self):
        # GIVEN
        data = {
            "name": "Completed",
            "tag": "completed",
            "color": "#0F0",
        }

        # WHEN
        ser = StatusSerializer(data=data)

        # THEN
        assert ser.is_valid()
        assert ser.data["color"] == data["color"]  # type: ignore

    def test_create_status(self):
        # GIVEN
        data = {
            "name": "In Progress",
            "description": "Task currently running",
            "tag": "in-progress",
            "color": "#FF5733",
        }

        # WHEN
        ser = StatusSerializer(data=data)
        assert ser.is_valid()
        status = ser.save()

        # THEN
        assert isinstance(status, Status)
        assert Status.objects.count() == 1
        assert status.name == data["name"]
        assert status.description == data["description"]
        assert status.tag == data["tag"]
        assert status.color == data["color"]

    def test_create_status_without_description(self):
        # GIVEN
        data = {
            "name": "Pending",
            "tag": "pending",
            "color": "#FFA500",
        }

        # WHEN
        ser = StatusSerializer(data=data)
        assert ser.is_valid()
        status = ser.save()

        # THEN
        assert isinstance(status, Status)
        assert Status.objects.count() == 1
        assert status.name == data["name"]
        assert status.description == ""
        assert status.tag == data["tag"]
        assert status.color == data["color"]

    def test_update_status(self):
        # GIVEN
        data = {
            "name": "In Progress",
            "description": "Task currently running",
            "tag": "in-progress",
            "color": "#FF5733",
        }
        updated_data = {
            "name": "Completed",
            "description": "Task completed successfully",
            "tag": "completed",
            "color": "#00FF00",
        }
        status = Status.objects.create(**data)

        # WHEN
        ser = StatusSerializer(instance=status, data=updated_data)
        assert ser.is_valid()
        status = ser.save()

        # THEN
        assert isinstance(status, Status)
        assert Status.objects.count() == 1
        assert status.name == updated_data["name"]
        assert status.description == updated_data["description"]
        assert status.tag == updated_data["tag"]
        assert status.color == updated_data["color"]

    def test_errors_missing_required_fields(self):
        # GIVEN
        data = {
            "description": "Description without name or tag",
            "color": "#FF5733",
        }

        # WHEN
        ser = StatusSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert ser.errors
        assert "name" in ser.errors
        assert "tag" in ser.errors

    def test_errors_invalid_color_format(self):
        # GIVEN
        data = {
            "name": "Test",
            "tag": "test",
            "color": "invalid-color",
        }

        # WHEN
        ser = StatusSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "color" in ser.errors

    def test_errors_invalid_color_without_hash(self):
        # GIVEN
        data = {
            "name": "Test",
            "tag": "test",
            "color": "FF5733",
        }

        # WHEN
        ser = StatusSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "color" in ser.errors

    def test_errors_invalid_color_too_long(self):
        # GIVEN
        data = {
            "name": "Test",
            "tag": "test",
            "color": "#FF57331234",
        }

        # WHEN
        ser = StatusSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "color" in ser.errors

    def test_errors_invalid_tag_with_spaces(self):
        # GIVEN
        data = {
            "name": "Test",
            "tag": "invalid tag with spaces",
            "color": "#FF5733",
        }

        # WHEN
        ser = StatusSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "tag" in ser.errors


@pytest.mark.django_db
class TestStatusReadOnlySerializer:
    def test_cannot_create_status(self):
        # GIVEN
        status_count_before = Status.objects.count()
        data = {
            "name": "In Progress",
            "description": "Task currently running",
            "tag": "in-progress",
            "color": "#FF5733",
        }

        # WHEN
        ser = StatusReadOnlySerializer(data=data)
        assert ser.is_valid()
        with pytest.raises(NotImplementedError):
            ser.save()

        # THEN
        assert Status.objects.count() == status_count_before

    def test_cannot_update_status(self):
        # GIVEN
        data = {
            "name": "In Progress",
            "description": "Task currently running",
            "tag": "in-progress",
            "color": "#FF5733",
        }
        status = Status.objects.create(**data)
        updated_data = {
            "name": "Completed",
            "description": "Task completed",
            "tag": "completed",
            "color": "#00FF00",
        }

        # WHEN
        ser = StatusReadOnlySerializer(instance=status, data=updated_data)
        assert ser.is_valid()
        with pytest.raises(NotImplementedError):
            ser.save()

    def test_serialize_status(self):
        # GIVEN
        data = {
            "name": "In Progress",
            "description": "Task currently running",
            "tag": "in-progress",
            "color": "#FF5733",
        }
        status = Status.objects.create(**data)
        expected = {
            "id": status.pk,
            "name": "In Progress",
            "description": "Task currently running",
            "tag": "in-progress",
            "color": "#FF5733",
            "is_ready": True,
        }

        # WHEN
        ser = StatusReadOnlySerializer(instance=status)

        # THEN
        assert ser.data == expected

    def test_serialize_status_without_description(self):
        # GIVEN
        data = {
            "name": "Pending",
            "tag": "pending",
            "color": "#FFA500",
        }
        status = Status.objects.create(**data)
        expected = {
            "id": status.pk,
            "name": "Pending",
            "description": "",
            "tag": "pending",
            "color": "#FFA500",
            "is_ready": True,
        }

        # WHEN
        ser = StatusReadOnlySerializer(instance=status)

        # THEN
        assert ser.data == expected


@pytest.mark.django_db
class TestStatusSeederSerializer:

    def test_valid_serializer(self):
        # GIVEN
        data = {
            "name": "In Progress",
            "description": "Task currently running",
            "tag": "in-progress",
            "color": "#FF5733",
            "seed_id": 1,
            "is_ready": True,
        }

        # WHEN
        ser = StatusSeederSerializer(data=data)

        # THEN
        assert ser.is_valid()

    def test_valid_serializer_without_is_ready_defaults_to_true(self):
        # GIVEN
        data = {
            "name": "Pending",
            "tag": "pending",
            "seed_id": 2,
        }

        # WHEN
        ser = StatusSeederSerializer(data=data)

        # THEN
        assert ser.is_valid()
        assert ser.data["is_ready"] is True

    def test_create_status_with_seeder_fields(self):
        # GIVEN
        data = {
            "name": "In Progress",
            "tag": "in-progress",
            "color": "#FF5733",
            "seed_id": 10,
            "is_ready": False,
        }

        # WHEN
        ser = StatusSeederSerializer(data=data)
        assert ser.is_valid()
        status = ser.save()

        # THEN
        assert isinstance(status, Status)
        assert status.seed_id == 10
        assert status.is_ready is False

    def test_update_status_with_seeder_fields(self):
        # GIVEN
        status = Status.objects.create(name="Old", tag="old", seed_id=5)
        updated_data = {
            "name": "Updated",
            "tag": "updated",
            "seed_id": 5,
            "is_ready": False,
        }

        # WHEN
        ser = StatusSeederSerializer(instance=status, data=updated_data)
        assert ser.is_valid()
        updated_status = ser.save()

        # THEN
        assert updated_status.seed_id == 5
        assert updated_status.is_ready is False

    def test_errors_missing_seed_id(self):
        # GIVEN
        data = {
            "name": "Test",
            "tag": "test",
        }

        # WHEN
        ser = StatusSeederSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "seed_id" in ser.errors

    def test_errors_seed_id_zero(self):
        # GIVEN
        data = {
            "name": "Test",
            "tag": "test",
            "seed_id": 0,
        }

        # WHEN
        ser = StatusSeederSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "seed_id" in ser.errors

    def test_errors_seed_id_negative(self):
        # GIVEN
        data = {
            "name": "Test",
            "tag": "test",
            "seed_id": -1,
        }

        # WHEN
        ser = StatusSeederSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert "seed_id" in ser.errors
