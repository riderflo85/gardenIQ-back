from rest_framework.serializers import Serializer
from rest_framework.viewsets import ModelViewSet


class BaseAPIModelViewSet(ModelViewSet):
    serializer_class: type[Serializer]

    # Does read only serializers
    list_serializer_class: type[Serializer] | None = None
    detail_serializer_class: type[Serializer]

    def get_serializer_class(self):
        if self.action == "list":
            return self.list_serializer_class if self.list_serializer_class else self.detail_serializer_class
        elif self.action == "retrieve":
            return self.detail_serializer_class
        else:
            return self.serializer_class
