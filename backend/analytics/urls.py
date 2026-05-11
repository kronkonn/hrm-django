from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AttritionPredictionViewSet, EmployeeClusterViewSet,
    AnomalyViewSet, MetricForecastViewSet,
    run_analytics, dashboard_summary, get_recommendations, department_clusters,
)
from .export import export_analytics

router = DefaultRouter()
router.register('attrition', AttritionPredictionViewSet, basename='attrition')
router.register('clusters', EmployeeClusterViewSet, basename='cluster')
router.register('anomalies', AnomalyViewSet, basename='anomaly')
router.register('forecasts', MetricForecastViewSet, basename='forecast')

urlpatterns = [
    path('run/', run_analytics, name='run_analytics'),
    path('dashboard/', dashboard_summary, name='dashboard_summary'),
    path('recommendations/', get_recommendations, name='get_recommendations'),
    path('department-clusters/', department_clusters, name='department_clusters'),
    path('export/', export_analytics, name='export_analytics'),
    path('', include(router.urls)),   # router — последним, чтобы не перехватывал явные пути
]
