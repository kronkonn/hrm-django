from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, CourseAssignmentViewSet, CertificateViewSet

router = DefaultRouter()
router.register('courses',      CourseViewSet,          basename='course')
router.register('assignments',  CourseAssignmentViewSet, basename='assignment')
router.register('certificates', CertificateViewSet,     basename='certificate')

urlpatterns = [path('', include(router.urls))]
