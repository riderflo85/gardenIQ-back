from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.base.views.base import READ_ONLY_HTTP_METHODS
from gardeniq.hardware.models import Channel
from gardeniq.hardware.models import Pin
from gardeniq.hardware.serializers import ChannelReadOnlySerializer
from gardeniq.hardware.serializers import ChannelSerializer
from gardeniq.hardware.serializers import PinDetailReadOnlySerializer
from gardeniq.hardware.serializers import PinMinimalReadOnlySerializer
from gardeniq.hardware.serializers import PinSerializer


class ChannelAPIModelView(BaseAPIModelViewSet):
    """API view for Channel model.
    The view provides read-only access to the Channel model, allowing users to retrieve
    a list of channels or details of a specific channel.
    Disabled create, update, and delete operations because depend on type of microcontroller and the number
    of channels available on it.
    The channels are predefined by microcontroller datasheet and cannot be modified through the API.
    """

    serializer_class = ChannelSerializer
    detail_serializer_class = ChannelReadOnlySerializer
    queryset = Channel.objects.all()
    http_method_names = READ_ONLY_HTTP_METHODS


class PinAPIModelView(BaseAPIModelViewSet):
    """API view for Pin model.
    The view provides read-only access to the Pin model, allowing users to retrieve
    a list of pins or details of a specific pin.
    Disabled create, update, and delete operations because depend on type of microcontroller and the number
    of pins available on it.
    The pins are predefined by microcontroller datasheet and cannot be modified through the API.
    """

    serializer_class = PinSerializer
    list_serializer_class = PinMinimalReadOnlySerializer
    detail_serializer_class = PinDetailReadOnlySerializer
    queryset = Pin.objects.all()
    http_method_names = READ_ONLY_HTTP_METHODS

    def get_queryset(self):
        qs = super().get_queryset()

        select_related_fields = []
        prefetch_related_fields = []
        if self.action in ("list", "retrieve"):
            select_related_fields = ["channel_choiced"]
        if self.action == "retrieve":
            select_related_fields += ["device", "device__status"]
            prefetch_related_fields = ["channels_available"]

        if select_related_fields:
            qs = qs.select_related(*select_related_fields)
        if prefetch_related_fields:
            qs = qs.prefetch_related(*prefetch_related_fields)
        return qs
