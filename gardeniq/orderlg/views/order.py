from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.base.views import DisableAPIViewMixin
from gardeniq.base.views import FilterAPIViewMixin
from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import OrderDetailReadOnlySerializer
from gardeniq.orderlg.serializers import OrderListReadOnlySerializer
from gardeniq.orderlg.serializers import OrderSerializer


class OrderAPIModelView(FilterAPIViewMixin, DisableAPIViewMixin, BaseAPIModelViewSet):
    serializer_class = OrderSerializer
    list_serializer_class = OrderListReadOnlySerializer
    detail_serializer_class = OrderDetailReadOnlySerializer
    queryset = Order.objects.all()
    filterset_fields = ["action_type", "sensor", "controller", "is_enabled"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ("list", "retrieve"):
            qs = qs.select_related(
                "sensor",
                "controller",
            )
        return qs
