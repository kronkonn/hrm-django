from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, DepartmentViewSet, PositionViewSet

router = DefaultRouter()
router.register('list', EmployeeViewSet, basename='employee')
router.register('departments', DepartmentViewSet, basename='department')
router.register('positions', PositionViewSet, basename='position')

urlpatterns = [path('', include(router.urls))]
