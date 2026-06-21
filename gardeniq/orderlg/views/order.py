from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.base.views import DisableAPIViewMixin
from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import OrderDetailReadOnlySerializer
from gardeniq.orderlg.serializers import OrderListReadOnlySerializer
from gardeniq.orderlg.serializers import OrderSerializer


class OrderAPIModelView(DisableAPIViewMixin, BaseAPIModelViewSet):
    serializer_class = OrderSerializer
    list_serializer_class = OrderListReadOnlySerializer
    detail_serializer_class = OrderDetailReadOnlySerializer
    queryset = Order.objects.all()
