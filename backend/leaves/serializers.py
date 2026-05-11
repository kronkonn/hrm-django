from rest_framework import serializers
from .models import LeaveRequest, SickLeaveDetails


class SickLeaveDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SickLeaveDetails
        fields = ['id', 'sick_leave_number', 'issue_date', 'close_date', 'medical_institution', 'diagnosis_code']


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sick_details = SickLeaveDetailsSerializer(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = '__all__'

    def get_approved_by_name(self, obj):
        return str(obj.approved_by) if obj.approved_by else None
