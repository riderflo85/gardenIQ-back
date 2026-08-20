import json
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import List

from django.db.models import Model

from rest_framework.serializers import Serializer


class BaseSeeder:
    model: type[Model]
    serializer: type[Serializer]
    filename: str
    root_dir_source: Path
    # It's use to search object in database for update it
    search_field_name: List[str] = ["seed_id"]

    source_file: Path
    dependencies = []
    related_fields_name: Dict[str, List[str]] = {"FK": [], "M2M": []}

    def __init__(
        self, success_logger: Callable[[object], str | Any], error_logger: Callable[[object], str | Any]
    ) -> None:
        """Check if class attributs is set by children."""
        assert hasattr(self, "model"), (
            "Error missing `model` attribut to `BaseSeeder` class for %s" % self.__class__.__name__
        )
        assert issubclass(self.model, Model), (
            "Error `model` attribut must be a subclass of `Model` for %s" % self.__class__.__name__
        )
        assert hasattr(self, "serializer"), (
            "Error missing `serializer` attribut to `BaseSeeder` class for %s" % self.__class__.__name__
        )
        assert issubclass(self.serializer, Serializer), (
            "Error `serializer` attribut must be a subclass of `Serializer` for %s" % self.__class__.__name__
        )
        assert hasattr(self, "filename"), (
            "Error missing `filename` attribut to `BaseSeeder` class for %s" % self.__class__.__name__
        )
        assert hasattr(self, "root_dir_source"), (
            "Error missing `root_dir_source` attribut to `BaseSeeder` class for %s" % self.__class__.__name__
        )
        assert hasattr(self, "search_field_name"), (
            "Error missing `search_field_name` attribut to `BaseSeeder` class for %s" % self.__class__.__name__
        )

        self.success_logger = success_logger
        self.error_logger = error_logger

        # construct source file path
        self.source_file = self.root_dir_source.joinpath(
            "sources",
            self.filename,
        )

        self._get_related_fields()

    def _get_related_fields(self) -> None:
        """Populate the `related_fields_name` attribute with the related fields names of the model."""
        for field in self.model._meta.get_fields():
            if field.is_relation:
                if field.many_to_many:
                    self.related_fields_name["M2M"].append(field.name)
                elif field.one_to_many or field.one_to_one or field.many_to_one:
                    self.related_fields_name["FK"].append(field.name)

    def _update_data_with_real_related_objects(self, data: Dict) -> Dict:
        """Update the data with the real related objects from the database."""
        for field_name in self.related_fields_name["FK"]:
            if field_name in data and data[field_name] is not None:
                related_model = self.model._meta.get_field(field_name).related_model
                try:
                    related_obj = related_model.objects.get(seed_id=data[field_name])
                    data[field_name] = related_obj.pk
                except related_model.DoesNotExist:
                    self.error_logger(
                        f"❌ Related object for field `{field_name}` with id `{data[field_name]}` does not exist."
                    )
                    data[field_name] = None

        for field_name in self.related_fields_name["M2M"]:
            if field_name in data and data[field_name] is not None:
                related_model = self.model._meta.get_field(field_name).related_model
                related_objs = []
                for seed_id in data[field_name]:
                    try:
                        related_obj = related_model.objects.get(seed_id=seed_id)
                        related_objs.append(related_obj.pk)
                    except related_model.DoesNotExist:
                        self.error_logger(
                            f"❌ Related object for field `{field_name}` with id `{seed_id}` does not exist."
                        )
                data[field_name] = related_objs
        return data

    def _create_entries(self, data_source: List | Dict) -> None:
        """Create all database entries based on source file data."""
        if not isinstance(data_source, list):
            data_source = [data_source]
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
            try:
                filters = {f: d[f] for f in self.search_field_name}
                obj = self.model.objects.get(**filters)
            except self.model.DoesNotExist:
                self._create_entries([d])
                continue
            # Update database entrie with new data
            ser = self.serializer(instance=obj, data=d)
            if ser.is_valid(raise_exception=True):
                updated_entrie = ser.save()
                self.success_logger(f"✅ updated successfully entrie : {updated_entrie}")

    def seed(self, authorize_update: bool = False) -> None:
        """Fill the database with source file data.
        Source file data is a json file.
        """
        with self.source_file.open(mode="r", encoding="utf-8") as f:
            data = json.loads(f.read())
            data = self._update_data_with_real_related_objects(data)
            if self.model.objects.count() == 0:
                self._create_entries(data)
            elif authorize_update:
                self._update_entries(data)
            else:
                self.error_logger(
                    f"❌ the entries for `{self.model}` already exist and you have not set `authorize_update` argument !"
                )
