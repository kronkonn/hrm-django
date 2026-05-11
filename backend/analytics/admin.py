from django.contrib import admin
from .models import AttritionPrediction, EmployeeCluster, Anomaly, MetricForecast


@admin.register(AttritionPrediction)
class AttritionPredictionAdmin(admin.ModelAdmin):
    list_display = ['employee', 'risk_score', 'risk_label', 'predicted_at']
    list_filter = ['risk_label']
    ordering = ['-risk_score']


@admin.register(EmployeeCluster)
class EmployeeClusterAdmin(admin.ModelAdmin):
    list_display = ['employee', 'cluster_id', 'cluster_label', 'x_tsne', 'y_tsne']
    list_filter = ['cluster_id']


@admin.register(Anomaly)
class AnomalyAdmin(admin.ModelAdmin):
    list_display = ['employee', 'metric', 'value', 'severity', 'detected_at', 'is_resolved']
    list_filter = ['severity', 'is_resolved']


@admin.register(MetricForecast)
class MetricForecastAdmin(admin.ModelAdmin):
    list_display = ['metric', 'period', 'forecast_value', 'lower_bound', 'upper_bound']
    list_filter = ['metric']
