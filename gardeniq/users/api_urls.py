from django.urls import path, include
from knox import views as knox_views

from gardeniq.base.routers import ToggleObjectRouter
from gardeniq.users.views import UserAPIModelView, LoginView


router = ToggleObjectRouter()
router.register(
    r"users",
    UserAPIModelView,
    basename="users",
)

auth_urlpatterns = [
    path("login/", LoginView.as_view(), name="knox_login"),
    path("logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("logoutall/", knox_views.LogoutAllView.as_view(), name="knox_logoutall"),
]

urlpatterns = [
    path("auth/", include(auth_urlpatterns)),
    path("", include(router.urls)),
]
