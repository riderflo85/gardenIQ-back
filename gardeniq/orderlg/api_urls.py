from gardeniq.base.routers import ToggleObjectRouter
from gardeniq.orderlg import views

__all__ = ["urlpatterns"]

router = ToggleObjectRouter()
router.register(
    r"orders",
    views.OrderAPIModelView,
    basename="orders",
)

urlpatterns = router.urls
