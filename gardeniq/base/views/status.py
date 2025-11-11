from gardeniq.base.models import Status
from gardeniq.base.serializers import StatusReadOnlySerializer
from gardeniq.base.serializers import StatusSerializer
from gardeniq.base.views import BaseAPIModelViewSet


class StatusAPIModelView(BaseAPIModelViewSet):
    serializer_class = StatusSerializer
    detail_serializer_class = StatusReadOnlySerializer
    queryset = Status.objects.all()
