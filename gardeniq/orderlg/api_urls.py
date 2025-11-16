from gardeniq.base.routers import ToggleObjectRouter
from gardeniq.orderlg.views import ArgumentAPIModelView
from gardeniq.orderlg.views import OrderAPIModelView

__all__ = ["urlpatterns"]

router = ToggleObjectRouter()
router.register(
    r"arguments",
    ArgumentAPIModelView,
    basename="arguments",
)
router.register(
    r"orders",
    OrderAPIModelView,
    basename="orders",
)

urlpatterns = router.urls
