from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VacancyViewSet, CandidateViewSet, CandidateResumeView

router = DefaultRouter()
router.register('vacancies', VacancyViewSet, basename='vacancy')
router.register('candidates', CandidateViewSet, basename='candidate')

urlpatterns = [
    path('candidates/<int:pk>/resume/', CandidateResumeView.as_view(), name='candidate-resume'),
    path('', include(router.urls)),
]
