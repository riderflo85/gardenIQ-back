from django_filters.rest_framework import DjangoFilterBackend

from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.hardware.filters import ControllerFilter
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.serializers import ControllerCategoryDetailReadOnlySerializer
from gardeniq.hardware.serializers import ControllerCategoryListReadOnlySerializer
from gardeniq.hardware.serializers import ControllerCategorySerializer
from gardeniq.hardware.serializers import ControllerDetailReadOnlySerializer
from gardeniq.hardware.serializers import ControllerListReadOnlySerializer
from gardeniq.hardware.serializers import ControllerSerializer


class ControllerCategoryAPIModelView(BaseAPIModelViewSet):
    serializer_class = ControllerCategorySerializer
    list_serializer_class = ControllerCategoryListReadOnlySerializer
    detail_serializer_class = ControllerCategoryDetailReadOnlySerializer
    queryset = ControllerCategory.objects.all()


class ControllerAPIModelView(BaseAPIModelViewSet):
    serializer_class = ControllerSerializer
    list_serializer_class = ControllerListReadOnlySerializer
    detail_serializer_class = ControllerDetailReadOnlySerializer
    queryset = Controller.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = ControllerFilter

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            qs = qs.select_related(
                "category",
                "pin__device",
                "pin__device__status",
            )
        return qs
