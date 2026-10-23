from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import DeviceCategory
from gardeniq.hardware.serializers import DeviceCategoryDetailReadOnlySerializer
from gardeniq.hardware.serializers import DeviceCategoryListReadOnlySerializer
from gardeniq.hardware.serializers import DeviceCategorySerializer
from gardeniq.hardware.serializers import DeviceDetailReadOnlySerializer
from gardeniq.hardware.serializers import DeviceSerializer


class DeviceCategoryAPIModelView(BaseAPIModelViewSet):
    # TODO: Ticket TK-79 (backlog n°4) : supprimer une catégorie utilisée par un device lève une
    # `ProtectedError` (`Device.category` en `on_delete=PROTECT`) non gérée, donc une erreur 500.
    # Bien vérifier ce comportement lors du traitement du ticket (réponse 409 attendue et test de vue).
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
