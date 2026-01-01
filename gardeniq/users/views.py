from django.contrib.auth import get_user_model

from gardeniq.base.views import BaseAPIModelViewSet
from gardeniq.users.serializers import UserSerializer, UserReadOnlySerializer

User = get_user_model()

class UserAPIModelView(BaseAPIModelViewSet):
    serializer_class = UserSerializer
    detail_serializer_class = UserReadOnlySerializer
    queryset = User.objects.all().prefetch_related('groups', 'user_permissions')
