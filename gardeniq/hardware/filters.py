from django.db.models import QuerySet

from django_filters import rest_framework as filters

from gardeniq.hardware.models import Controller
from gardeniq.hardware.models import Device
from gardeniq.hardware.models import Pin
from gardeniq.hardware.models import Sensor


class PinFilter(filters.FilterSet):
    available = filters.BooleanFilter(method="filter_available", label="Not used by a sensor or a controller")

    class Meta:
        model = Pin
        fields = ["device", "available"]

    def filter_available(self, queryset: QuerySet[Pin], name: str, value: bool) -> QuerySet[Pin]:
        free = {"sensor__isnull": True, "controller__isnull": True}
        return queryset.filter(**free) if value else queryset.exclude(**free)


class SensorFilter(filters.FilterSet):
    device = filters.ModelChoiceFilter(field_name="pin__device", queryset=Device.objects.all())

    class Meta:
        model = Sensor
        fields = ["device", "category"]


class ControllerFilter(filters.FilterSet):
    device = filters.ModelChoiceFilter(field_name="pin__device", queryset=Device.objects.all())

    class Meta:
        model = Controller
        fields = ["device", "category"]
