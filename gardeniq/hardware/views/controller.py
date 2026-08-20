from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import ControllerCategory
from gardeniq.hardware.serializers import ControllerCategoryReadOnlySerializer
from gardeniq.hardware.serializers import ControllerCategorySerializer
from gardeniq.hardware.serializers import ControllerDetailReadOnlySerializer
from gardeniq.hardware.serializers import ControllerListReadOnlySerializer
from gardeniq.hardware.serializers import ControllerSerializer


class ControllerCategoryAPIModelView(BaseAPIModelViewSet):
    serializer_class = ControllerCategorySerializer
    detail_serializer_class = ControllerCategoryReadOnlySerializer
    queryset = ControllerCategory.objects.all()


class ControllerAPIModelView(BaseAPIModelViewSet):
    serializer_class = ControllerSerializer
    list_serializer_class = ControllerListReadOnlySerializer
    detail_serializer_class = ControllerDetailReadOnlySerializer
    queryset = Controller.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            qs = qs.select_related(
                "category",
                "device",
                "device__status",
                "pin",
            )
        return qs
