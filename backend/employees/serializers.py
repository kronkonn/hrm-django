from rest_framework import serializers
from .models import Employee, Department, Position


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = '__all__'

    def get_employee_count(self, obj):
        return obj.employees.filter(status='active').count()


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Position
        fields = '__all__'


def _leave_info(employee):
    """Returns (current_leave, upcoming_leave) dicts for an employee.

    Uses the prefetch_related('leave_requests') cache when available to avoid
    N+1 queries on list endpoints.
    """
    from datetime import date, timedelta

    today = date.today()
    threshold = today + timedelta(days=7)

    # Use prefetch cache if populated, otherwise hit DB directly
    try:
        leaves = employee.leave_requests.all()  # may use prefetch cache
        approved = [l for l in leaves if l.status == 'approved']
    except Exception:
        from leaves.models import LeaveRequest
        approved = list(LeaveRequest.objects.filter(employee=employee, status='approved'))

    current = next(
        (l for l in approved if l.start_date <= today <= l.end_date),
        None,
    )
    upcoming = None
    if not current:
        upcoming = next(
            (l for l in sorted(approved, key=lambda x: x.start_date)
             if today < l.start_date <= threshold),
            None,
        )

    def _fmt(leave):
        return {
            'start_date': leave.start_date.isoformat(),
            'end_date':   leave.end_date.isoformat(),
            'leave_type': leave.leave_type,
        }

    return (_fmt(current) if current else None, _fmt(upcoming) if upcoming else None)


class EmployeeListSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    full_name = serializers.CharField(read_only=True)
    current_leave = serializers.SerializerMethodField()
    upcoming_leave = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'full_name', 'first_name', 'last_name', 'email',
            'department', 'department_name', 'position', 'position_title',
            'status', 'hire_date', 'salary', 'photo',
            'current_leave', 'upcoming_leave',
        ]

    def get_current_leave(self, obj):
        return _leave_info(obj)[0]

    def get_upcoming_leave(self, obj):
        return _leave_info(obj)[1]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    full_name = serializers.CharField(read_only=True)
    manager_name = serializers.SerializerMethodField()
    hours_fulfillment = serializers.SerializerMethodField()
    current_leave = serializers.SerializerMethodField()
    upcoming_leave = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = '__all__'

    def get_manager_name(self, obj):
        return str(obj.manager) if obj.manager else None

    def get_hours_fulfillment(self, obj):
        return obj.hours_fulfillment

    def get_current_leave(self, obj):
        return _leave_info(obj)[0]

    def get_upcoming_leave(self, obj):
        return _leave_info(obj)[1]
