from rest_framework.routers import DefaultRouter

from gardeniq.base.views import StatusAPIModelView

router = DefaultRouter()
router.register(
    r"status",
    StatusAPIModelView,
    basename="status",

)

urlpatterns = router.urls
