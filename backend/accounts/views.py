from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserMeSerializer,
    UserListSerializer,
    UserRoleUpdateSerializer,
    ProfileUpdateSerializer,
)
from .models import UserProfile
from .permissions import IsAdmin


class CustomTokenObtainPairView(TokenObtainPairView):
    """Логин: возвращает токены + role + employee_id."""
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """Текущий пользователь и его роль."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserMeSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if 'password' in data:
            request.user.set_password(data['password'])
            request.user.save(update_fields=['password'])
        return Response({'status': 'ok'})


class UserListView(APIView):
    """GET /api/auth/users/ — список всех пользователей (только ADMIN)."""
    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.select_related('profile').order_by('id')
        return Response(UserListSerializer(users, many=True).data)


class UserRoleUpdateView(APIView):
    """PATCH /api/auth/users/{id}/ — изменить роль пользователя (только ADMIN)."""
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_role = serializer.validated_data['role']

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=404)

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = new_role
        profile.save(update_fields=['role'])
        return Response({'status': 'ok', 'role': new_role})


class UserChangePasswordView(APIView):
    """POST /api/auth/users/{id}/change_password/ — сменить пароль пользователю (только ADMIN)."""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        password = request.data.get('password', '')
        if len(password) < 6:
            return Response({'detail': 'Пароль должен быть не короче 6 символов.'}, status=400)
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=404)
        user.set_password(password)
        user.save(update_fields=['password'])
        return Response({'status': 'ok'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """POST /api/auth/logout/ — фиксирует выход (JWT stateless, middleware залогирует LOGOUT)."""
    return Response({'status': 'logged_out'})
