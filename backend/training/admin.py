from django.contrib import admin
from .models import Course, CourseAssignment, Certificate


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'duration_hours', 'deadline', 'status', 'created_by')
    list_filter = ('category', 'status')
    search_fields = ('title',)


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'course', 'status', 'progress', 'assigned_at', 'completed_at')
    list_filter = ('status',)
    search_fields = ('employee__last_name', 'course__title')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'employee', 'course', 'issued_at')
    search_fields = ('certificate_number', 'employee__last_name')
