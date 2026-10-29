from gardeniq.base.models import Status
from gardeniq.base.serializers import StatusReadOnlySerializer
from gardeniq.base.serializers import StatusSerializer
from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.base.views import FilterAPIViewMixin


class StatusAPIModelView(FilterAPIViewMixin, BaseAPIModelViewSet):
    serializer_class = StatusSerializer
    detail_serializer_class = StatusReadOnlySerializer
    queryset = Status.objects.all()
    filterset_fields = ["tag"]
