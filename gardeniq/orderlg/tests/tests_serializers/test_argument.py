import pytest

from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.serializers import ArgumentSerializer


@pytest.mark.django_db
class TestArgumentSerializer:

    def test_valide_serializer(self):
        # GIVEN
        data = {
            "description": "my description, blabla",
            "slug": "my-description-blabla",
            "value_type": "int",
        }
        expected = {
            "description": "my description, blabla",
            "slug": "my-description-blabla",
            "is_enabled": True,
            "value_type": "int",
            "required": True,
            "is_option": False,
        }

        # WHEN
        ser = ArgumentSerializer(data=data)

        # THEN
        assert ser.is_valid()
        assert ser.data == expected

    def test_create_argument(self):
        # GIVEN
        data = {
            "description": "my description, blabla",
            "slug": "my-description-blabla",
            "value_type": "int",
        }

        # WHEN
        ser = ArgumentSerializer(data=data)
        assert ser.is_valid()
        argument = ser.save()

        # THEN
        assert isinstance(argument, Argument)
        assert Argument.objects.count() == 1
        assert argument.description == "my description, blabla"
        assert argument.slug == "my-description-blabla"
        assert argument.value_type == "int"
        assert argument.required is True
        assert argument.is_option is False

    def test_update_argument(self):
        # GIVEN
        data = {
            "description": "my description, blabla",
            "slug": "my-description-blabla",
            "value_type": "int",
        }
        updated_data = {
            "description": "my new description, toto",
            "slug": "my-new-description-toto",
            "value_type": "float",
            "required": False,
            "is_option": True,
        }
        argument = Argument.objects.create(**data)

        # WHEN
        ser = ArgumentSerializer(instance=argument, data=updated_data)
        assert ser.is_valid()
        argument = ser.save()

        # THEN
        assert isinstance(argument, Argument)
        assert Argument.objects.count() == 1
        assert argument.description == updated_data["description"]
        assert argument.slug == updated_data["slug"]
        assert argument.value_type == updated_data["value_type"]
        assert argument.required is False
        assert argument.is_option is True

    def test_errors_serializer(self):
        # GIVEN
        data = {
            "description": "my description, blabla",
            # "slug": "my-description-blabla",
            "value_type": "invalid",
        }

        # WHEN
        ser = ArgumentSerializer(data=data)

        # THEN
        assert not ser.is_valid()
        assert ser.errors
        assert "value_type" in ser.errors
        assert "slug" in ser.errors
