from django.contrib import admin
from .models import Timesheet


@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'work_date', 'day_type', 'hours_worked', 'overtime_hours']
    list_filter   = ['day_type', 'work_date', 'employee__department']
    search_fields = ['employee__last_name', 'employee__first_name']
    date_hierarchy = 'work_date'
