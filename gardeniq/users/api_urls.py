from gardeniq.base.routers import ToggleObjectRouter
from gardeniq.users.views import UserAPIModelView

router = ToggleObjectRouter()
router.register(
    r"users",
    UserAPIModelView,
    basename="users",
)

urlpatterns = router.urls
