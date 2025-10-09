from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.base.views import DisableAPIViewMixin
from gardeniq.orderlg.models import Argument
from gardeniq.orderlg.models import Order
from gardeniq.orderlg.serializers import ArgumentReadOnlySerializer
from gardeniq.orderlg.serializers import ArgumentSerializer
from gardeniq.orderlg.serializers import OrderDetailReadOnlySerializer
from gardeniq.orderlg.serializers import OrderSerializer


class ArgumentAPIModelView(DisableAPIViewMixin, BaseAPIModelViewSet):
    serializer_class = ArgumentSerializer
    detail_serializer_class = ArgumentReadOnlySerializer
    queryset = Argument.objects.all()


class OrderAPIModelView(DisableAPIViewMixin, BaseAPIModelViewSet):
    serializer_class = OrderSerializer
    detail_serializer_class = OrderDetailReadOnlySerializer
    queryset = Order.objects.none()

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.prefetch_related("arguments")
        return qs
