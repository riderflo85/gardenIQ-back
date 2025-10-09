from typing import Dict

from django.db.models import Model

from rest_framework.reverse import reverse
from rest_framework.test import APIClient

import pytest


class ViewSetTestMixin:
    """A mixin class providing utility methods and fixtures for testing Django REST Framework ViewSets.

    Attributes:
        BASE_PATTERN (str): The base pattern name used for URL reversing.
        MODEL (type[Model]): The Django model class associated with the ViewSet.
        DATA_TO_DEFAULT_OBJ (Dict): Default data used to create a model instance for testing.

    Fixtures:
        client_anonymous() -> APIClient:
            Returns an anonymous APIClient instance for testing.

        obj() -> type[Model]:
            Returns a default model instance for use in tests.
    """
    BASE_PATTERN: str = ""
    MODEL: type[Model]
    DATA_TO_DEFAULT_OBJ: Dict

    def _return_obj_id(self, obj: type[Model] | int) -> int:
        """
        Returns the primary key (ID) of a given object.

        If the input is an integer, it is assumed to be the primary key and returned as is.
        If the input is a Django model instance, its primary key (`pk` attribute) is returned.

        Args:
            obj (type[Model] | int): A Django model instance or an integer representing the primary key.

        Returns:
            int: The primary key of the object.
        """
        if isinstance(obj, int):
            pk = obj
        else:
            pk = obj.pk
        return pk

    def get_url_list(self):
        return reverse(f"{self.BASE_PATTERN}-list")

    def get_url_create(self):
        return self.get_url_list()

    def get_url_detail(self, obj: type[Model] | int):
        pk = self._return_obj_id(obj)
        return reverse(f"{self.BASE_PATTERN}-detail", kwargs={"pk": pk})

    def get_url_enable(self, obj: type[Model] | int):
        pk = self._return_obj_id(obj)
        return reverse(f"{self.BASE_PATTERN}-enable", kwargs={"pk": pk})

    def get_url_disable(self, obj: type[Model] | int):
        pk = self._return_obj_id(obj)
        return reverse(f"{self.BASE_PATTERN}-disable", kwargs={"pk", pk})

    def generate_default_obj(self) -> type[Model]:
        new_obj = self.MODEL.objects.create(**self.DATA_TO_DEFAULT_OBJ)
        return new_obj  # type: ignore

    @pytest.fixture
    def client_anonymous(self) -> APIClient:
        client = APIClient()
        client.force_authenticate(None)
        return client

    @pytest.fixture
    def obj(self) -> type[Model]:
        return self.generate_default_obj()
