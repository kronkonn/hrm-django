from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    MeView,
    UserListView,
    UserRoleUpdateView,
    UserChangePasswordView,
    logout_view,
)

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout_view, name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', UserRoleUpdateView.as_view(), name='user_role_update'),
    path('users/<int:pk>/change_password/', UserChangePasswordView.as_view(), name='user_change_password'),
]
