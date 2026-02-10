from django.contrib.auth import login

from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle

from knox.views import LoginView as KnoxLoginView


class LoginThrottle(AnonRateThrottle):
    rate = "5/min"


class LoginView(KnoxLoginView):
    """
    Custom login view that returns user data along with the token.
    POST /api/login/
    Body: {"username": "user", "password": "pass"}
    Returns: token, user data, expiry
    """

    throttle_classes = [LoginThrottle]
    permission_classes = [AllowAny]
    serializer_class = AuthTokenSerializer

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]  # type: ignore
        login(request, user)
        return super(LoginView, self).post(request, format=None)
