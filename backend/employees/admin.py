from django.contrib import admin
from .models import Employee, Department, Position


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'salary_min', 'salary_max']
    list_filter = ['department']
    search_fields = ['title']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'department', 'position', 'status', 'hire_date']
    list_filter = ['status', 'department', 'gender']
    search_fields = ['first_name', 'last_name', 'email']
    date_hierarchy = 'hire_date'
