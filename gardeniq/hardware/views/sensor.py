from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.base.views import FilterAPIViewMixin
from gardeniq.hardware.filters import SensorFilter
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory
from gardeniq.hardware.serializers import SensorCategoryDetailReadOnlySerializer
from gardeniq.hardware.serializers import SensorCategoryListReadOnlySerializer
from gardeniq.hardware.serializers import SensorCategorySerializer
from gardeniq.hardware.serializers import SensorDetailReadOnlySerializer
from gardeniq.hardware.serializers import SensorListReadOnlySerializer
from gardeniq.hardware.serializers import SensorSerializer


class SensorCategoryAPIModelView(BaseAPIModelViewSet):
    serializer_class = SensorCategorySerializer
    list_serializer_class = SensorCategoryListReadOnlySerializer
    detail_serializer_class = SensorCategoryDetailReadOnlySerializer
    queryset = SensorCategory.objects.all()


class SensorAPIModelView(FilterAPIViewMixin, BaseAPIModelViewSet):
    serializer_class = SensorSerializer
    list_serializer_class = SensorListReadOnlySerializer
    detail_serializer_class = SensorDetailReadOnlySerializer
    queryset = Sensor.objects.all()
    filterset_class = SensorFilter

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            qs = qs.select_related(
                "category",
                "pin__device",
                "pin__device__status",
            )
        return qs
