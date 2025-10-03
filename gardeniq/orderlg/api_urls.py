from gardeniq.base.routers import ToggleObjectRouter
from gardeniq.orderlg.views import ArgumentModelView
from gardeniq.orderlg.views import OrderModelView

router = ToggleObjectRouter()
router.register(
    r"arguments",
    ArgumentModelView,
    basename="arguments",
)
router.register(
    r"orders",
    OrderModelView,
    basename="orders",
)

urlpatterns = router.urls
