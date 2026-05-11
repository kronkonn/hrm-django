from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TimesheetViewSet

router = DefaultRouter()
router.register('', TimesheetViewSet, basename='timesheet')
urlpatterns = [path('', include(router.urls))]
