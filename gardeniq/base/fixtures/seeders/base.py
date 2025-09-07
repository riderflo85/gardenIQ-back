from pathlib import Path
from typing import Any
from typing import Callable

from django.db.models import Model

from rest_framework.parsers import JSONParser
from rest_framework.serializers import ModelSerializer


class BaseSeeder:
    model: type[Model]
    serializer: type[ModelSerializer]
    filename: str
    root_dir_source: Path
    # It's use to search object in database for update it
    search_field_name: str

    source_file: Path
    dependencies = []

    def __init__(
        self, success_logger: Callable[[object], str | Any], error_logger: Callable[[object], str | Any]
    ) -> None:
        """Check if class attributs is set by children."""
        assert issubclass(self.serializer, ModelSerializer)
        assert issubclass(self.model, Model)
        assert isinstance(self.root_dir_source, Path)
        assert isinstance(self.filename, str)
        assert isinstance(self.search_field_name, str)

        self.success_logger = success_logger
        self.error_logger = error_logger

        # construct source file path
        self.source_file = self.root_dir_source.joinpath(
            "sources",
            self.filename,
        )

    def _create_entries(self, data_source) -> None:
        """Create all database entries based on source file data."""
        for d in data_source:
            ser = self.serializer(data=d)
            if ser.is_valid(raise_exception=True):
                new_entrie = ser.save()
                self.success_logger(f"✅ create successfully entrie : {new_entrie}")

    def _update_entries(self, data_source) -> None:
        """Update database entries based on source file data."""
        for d in data_source:
            # Get entrie database with `search_field_name` table field.
            #   Because `search_field_name` is a string, doesn't use .get("field_name"="value") it's not work !
            #   Create a dict {"field_name": "value"} and use `**` to unpack dict.
            obj = self.model.objects.get(**{self.search_field_name: d[self.search_field_name]})

            # Update database entrie with new data
            ser = self.serializer(obj, data=d)
            if ser.is_valid(raise_exception=True):
                updated_entrie = ser.save()
                self.success_logger(f"✅ updated successfully entrie : {updated_entrie}")

    def seed(self, authorize_update: bool = False) -> None:
        """Fill the database with source file data.
        Source file data is a json file.
        """
        with self.source_file.open(mode="r") as f:
            data = JSONParser().parse(f)
            if self.model.objects.count() == 0:
                self._create_entries(data)
            elif authorize_update:
                self._update_entries(data)
            else:
                self.error_logger(
                    f"❌ the entries for `{self.model}` already exist and you have not set `authorize_update` argument !"
                )
