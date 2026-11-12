from django.contrib.auth import login

from rest_framework import status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from drf_spectacular.utils import extend_schema
from knox.views import LoginView as KnoxLoginView


class LoginThrottle(AnonRateThrottle):
    rate = "5/min"


@extend_schema(
    request=AuthTokenSerializer,
)
class LoginView(KnoxLoginView):
    """
    Custom login view that returns user data along with the token.
    POST /api/auth/login/
    Body: {"username": "user", "password": "pass"}
    Returns: token, user data, expiry
    """

    throttle_classes = [LoginThrottle]
    permission_classes = [AllowAny]
    serializer_class = AuthTokenSerializer

    def post(self, request: Request, format: str | None = None) -> Response:
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]  # type: ignore
        # `login` is typed for a Django HttpRequest: the DRF Request wraps one and must get the user, knox reads it.
        login(request, user)  # pyright: ignore[reportArgumentType]
        response = super(LoginView, self).post(request, format=None)
        # Knox returns its token limit error as a plain 403 response: raise it so it gets the API error body.
        if response.status_code == status.HTTP_403_FORBIDDEN and response.data:
            raise PermissionDenied(response.data["error"])
        return response
