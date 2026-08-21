from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.serializers import DeviceCategoryDetailReadOnlySerializer
from gardeniq.hardware.serializers import DeviceCategoryListReadOnlySerializer
from gardeniq.hardware.serializers import DeviceCategorySerializer
from gardeniq.hardware.serializers import DeviceDetailReadOnlySerializer
from gardeniq.hardware.serializers import DeviceSerializer


class DeviceCategoryAPIModelView(BaseAPIModelViewSet):
    serializer_class = DeviceCategorySerializer
    list_serializer_class = DeviceCategoryListReadOnlySerializer
    detail_serializer_class = DeviceCategoryDetailReadOnlySerializer
    queryset = DeviceCategory.objects.all()


class DeviceAPIModelView(BaseAPIModelViewSet):
    serializer_class = DeviceSerializer
    detail_serializer_class = DeviceDetailReadOnlySerializer
    queryset = Device.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            qs = qs.select_related("category", "status")
        return qs
