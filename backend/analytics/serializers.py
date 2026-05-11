from rest_framework import serializers
from .models import AttritionPrediction, EmployeeCluster, Anomaly, MetricForecast


class AttritionPredictionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True)

    class Meta:
        model = AttritionPrediction
        fields = '__all__'


class EmployeeClusterSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True)

    class Meta:
        model = EmployeeCluster
        fields = '__all__'


class AnomalySerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = Anomaly
        fields = '__all__'

    def get_employee_name(self, obj):
        return str(obj.employee) if obj.employee else None


class MetricForecastSerializer(serializers.ModelSerializer):
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)

    class Meta:
        model = MetricForecast
        fields = '__all__'
