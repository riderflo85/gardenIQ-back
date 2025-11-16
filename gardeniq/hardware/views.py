from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.hardware.models import Device
from gardeniq.hardware.serializers import DeviceDetailReadOnlySerializer
from gardeniq.hardware.serializers import DeviceSerializer


class DeviceAPIModelView(BaseAPIModelViewSet):
    serializer_class = DeviceSerializer
    detail_serializer_class = DeviceDetailReadOnlySerializer
    queryset = Device.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related("status")
        return qs
