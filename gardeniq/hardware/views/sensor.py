from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.hardware.models import Sensor
from gardeniq.hardware.models import SensorCategory
from gardeniq.hardware.serializers import SensorCategoryReadOnlySerializer
from gardeniq.hardware.serializers import SensorCategorySerializer
from gardeniq.hardware.serializers import SensorDetailReadOnlySerializer
from gardeniq.hardware.serializers import SensorListReadOnlySerializer
from gardeniq.hardware.serializers import SensorSerializer


class SensorCategoryAPIModelView(BaseAPIModelViewSet):
    serializer_class = SensorCategorySerializer
    detail_serializer_class = SensorCategoryReadOnlySerializer
    queryset = SensorCategory.objects.all()


class SensorAPIModelView(BaseAPIModelViewSet):
    serializer_class = SensorSerializer
    list_serializer_class = SensorListReadOnlySerializer
    detail_serializer_class = SensorDetailReadOnlySerializer
    queryset = Sensor.objects.all()

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
