"""
Management command: sync employee statuses based on approved leave requests.

Run manually:   python manage.py update_leave_statuses
Cron (daily):   0 0 * * * /path/venv/bin/python /path/manage.py update_leave_statuses
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Sync employee statuses with approved leave requests'

    def handle(self, *args, **options):
        from employees.models import Employee
        from leaves.models import LeaveRequest

        today = date.today()

        # 1. Employees whose approved leave covers today → on_leave
        active_leave_emp_ids = set(
            LeaveRequest.objects.filter(
                status='approved',
                start_date__lte=today,
                end_date__gte=today,
            ).values_list('employee_id', flat=True)
        )
        started = Employee.objects.filter(
            pk__in=active_leave_emp_ids,
            status='active',
        ).update(status='on_leave')

        # 2. Employees marked on_leave but no active leave covers today → active
        on_leave_ids = set(
            Employee.objects.filter(status='on_leave').values_list('pk', flat=True)
        )
        should_return = on_leave_ids - active_leave_emp_ids
        returned = Employee.objects.filter(pk__in=should_return).update(status='active')

        self.stdout.write(
            self.style.SUCCESS(
                f'[{today}] Started leave: {started}, Returned to active: {returned}'
            )
        )
