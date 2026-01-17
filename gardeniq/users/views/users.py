from django.contrib.auth import get_user_model

from rest_framework.permissions import IsAuthenticated, BasePermission, IsAdminUser
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from gardeniq.users.serializers import UserSerializer, UserReadOnlySerializer, UserDetailReadOnlySerializer

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


class UserAPIModelView(ModelViewSet):
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
    queryset = User.objects.all().prefetch_related("groups", "user_permissions")
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_permissions(self):
        """
        Different permissions based on action.
        """
        if self.action == "retrieve":
            # Owner or admin
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == "update":
            # Owner can modify their profile, admin can all
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        # elif self.action == "create":
        #     if self.queryset.count() == 0:
        #         # Allow creation if no users exist (initial setup)
        #         permission_classes = [AllowAny]
        #     else:
        #         permission_classes = [IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Different serializers based on action.
        """
        if self.action == "retrieve":
            return UserDetailReadOnlySerializer
        elif self.action == "list":
            return UserReadOnlySerializer
        return UserSerializer

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get the information of the authenticated user.
        """
        serializer = UserDetailReadOnlySerializer(request.user)
        return Response(serializer.data)
