from django.urls import include
from django.urls import path

from rest_framework.routers import DefaultRouter

from knox import views as knox_views

from gardeniq.users.views import LoginView
from gardeniq.users.views import UserAPIModelView

router = DefaultRouter()
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
