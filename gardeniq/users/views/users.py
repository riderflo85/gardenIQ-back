from django.contrib.auth import get_user_model

from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from gardeniq.base.views.base import BaseAPIModelViewSet
from gardeniq.users.serializers import UserDetailReadOnlySerializer
from gardeniq.users.serializers import UserReadOnlySerializer
from gardeniq.users.serializers import UserSerializer

User = get_user_model()


class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission: owner or admin.
    """

    def has_object_permission(self, request, view, obj):
        # Admins have all rights
        if request.user.is_staff:
            return True
        # Modification only by owner
        return obj == request.user


class UserAPIModelView(BaseAPIModelViewSet):
    """
    ViewSet CRUD for users.

    list: GET /api/users/ - List all users (admin only)
    retrieve: GET /api/users/{id}/ - User details (self detail if not admin or any if is admin)
    create: POST /api/users/ - Create a user (admin only)
    update: PUT /api/users/{id}/ - Update a user (admin only)
    partial_update: Not allowed
    destroy: DELETE /api/users/{id}/ - Delete a user (admin only)
    me: GET /api/users/me/ - Get authenticated user info
    """

    serializer_class = UserSerializer
    list_serializer_class = UserReadOnlySerializer
    detail_serializer_class = UserDetailReadOnlySerializer
    queryset = User.objects.all().prefetch_related("groups", "user_permissions")

    def get_permissions(self):
        """
        Different permissions based on action.
        """
        # Check if this is a request to /me/ endpoint (for any HTTP method)
        if self.action == "me" or (hasattr(self, "request") and "/me/" in self.request.path):
            # Any authenticated user can access their own profile
            permission_classes = [IsAuthenticated]
        elif self.action in ("retrieve", "update"):
            # Owner or admin
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

        # TODO: À revoir plus tard pour séparer la création du premier compte (dans un autre endpoint API)
        # Mais laisser la possibilité de créer un nouveau compte user à partir d'ici

        # elif self.action == "create":
        #     if self.queryset.count() == 0:
        #         # Allow creation if no users exist (initial setup)
        #         permission_classes = [AllowAny]
        #     else:
        #         permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get"])
    def me(self, request):
        """
        Get the information of the authenticated user.
        """
        serializer = UserDetailReadOnlySerializer(request.user)
        return Response(serializer.data)
