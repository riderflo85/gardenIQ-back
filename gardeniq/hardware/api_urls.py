from rest_framework.routers import DefaultRouter

from gardeniq.hardware.views import DeviceAPIModelView

router = DefaultRouter()
router.register(
    r"devices",
    DeviceAPIModelView,
    basename="devices",
)

urlpatterns = router.urls
