from rest_framework import serializers
from .models import Timesheet


class TimesheetSerializer(serializers.ModelSerializer):
    employee_name      = serializers.CharField(source='employee.full_name', read_only=True)
    department_name    = serializers.CharField(source='employee.department.name', read_only=True)
    day_type_display   = serializers.CharField(source='get_day_type_display', read_only=True)

    class Meta:
        model  = Timesheet
        fields = [
            'id', 'employee', 'employee_name', 'department_name',
            'work_date', 'day_type', 'day_type_display',
            'hours_worked', 'overtime_hours', 'note',
            'created_at', 'updated_at',
        ]
