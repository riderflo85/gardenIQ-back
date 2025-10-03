from rest_framework.serializers import Serializer
from rest_framework.viewsets import ModelViewSet


class BaseAPIModelViewSet(ModelViewSet):
    serializer_class: type[Serializer]
    # Does read only serializer
    detail_serializer_class: type[Serializer]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return self.detail_serializer_class
        else:
            return self.serializer_class
