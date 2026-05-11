from rest_framework import serializers
from .models import Course, CourseAssignment, Certificate


class CourseSerializer(serializers.ModelSerializer):
    created_by_name   = serializers.SerializerMethodField()
    category_display  = serializers.CharField(source='get_category_display', read_only=True)
    status_display    = serializers.CharField(source='get_status_display', read_only=True)
    assignments_count = serializers.SerializerMethodField()
    completed_count   = serializers.SerializerMethodField()
    lessons_count     = serializers.SerializerMethodField()

    class Meta:
        model  = Course
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_assignments_count(self, obj):
        return obj.assignments.count()

    def get_completed_count(self, obj):
        return obj.assignments.filter(status='completed').count()

    def get_lessons_count(self, obj):
        return len(obj.lessons or [])


class CourseAssignmentSerializer(serializers.ModelSerializer):
    employee_name   = serializers.CharField(source='employee.full_name', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True)
    course_title    = serializers.CharField(source='course.title', read_only=True)
    course_category = serializers.CharField(source='course.category', read_only=True)
    course_deadline = serializers.DateField(source='course.deadline', read_only=True)
    course_duration = serializers.IntegerField(source='course.duration_hours', read_only=True)
    lessons_count   = serializers.SerializerMethodField()
    status_display  = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = CourseAssignment
        fields = '__all__'

    def get_lessons_count(self, obj):
        return len(obj.course.lessons or [])


class CourseAssignmentDetailSerializer(CourseAssignmentSerializer):
    """Extends list serializer with full lesson content — used on retrieve."""
    course_lessons = serializers.JSONField(source='course.lessons', read_only=True)

    class Meta(CourseAssignmentSerializer.Meta):
        pass


class CertificateSerializer(serializers.ModelSerializer):
    employee_name   = serializers.CharField(source='employee.full_name', read_only=True)
    course_title    = serializers.CharField(source='course.title', read_only=True)
    course_category = serializers.CharField(source='course.category', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True)

    class Meta:
        model  = Certificate
        fields = '__all__'
