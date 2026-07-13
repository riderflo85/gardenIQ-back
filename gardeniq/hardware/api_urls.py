from rest_framework.routers import DefaultRouter

from gardeniq.hardware.views import ChannelAPIModelView
from gardeniq.hardware.views import ControllerAPIModelView
from gardeniq.hardware.views import ControllerCategoryAPIModelView
from gardeniq.hardware.views import DeviceAPIModelView
from gardeniq.hardware.views import PinAPIModelView
from gardeniq.hardware.views import SensorAPIModelView
from gardeniq.hardware.views import SensorCategoryAPIModelView

__all__ = ["urlpatterns"]

router = DefaultRouter()
router.register(
    r"devices",
    DeviceAPIModelView,
    basename="devices",
)
router.register(
    r"controllers",
    ControllerAPIModelView,
    basename="controllers",
)
router.register(
    r"controller-categories",
    ControllerCategoryAPIModelView,
    basename="controller-categories",
)
router.register(
    r"sensors",
    SensorAPIModelView,
    basename="sensors",
)
router.register(
    r"sensor-categories",
    SensorCategoryAPIModelView,
    basename="sensor-categories",
)
router.register(
    r"pins",
    PinAPIModelView,
    basename="pins",
)
router.register(
    r"channels",
    ChannelAPIModelView,
    basename="channels",
)

urlpatterns = router.urls
