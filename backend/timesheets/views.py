import calendar
from datetime import date, timedelta

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from accounts.permissions import IsHROrDirector
from employees.models import Employee
from leaves.models import LeaveRequest
from .models import Timesheet
from .serializers import TimesheetSerializer


class NoPagination(PageNumberPagination):
    page_size = None


class TimesheetViewSet(viewsets.ModelViewSet):
    queryset           = Timesheet.objects.select_related('employee', 'employee__department').all()
    serializer_class   = TimesheetSerializer
    permission_classes = [IsHROrDirector]
    filter_backends    = [filters.OrderingFilter]
    ordering           = ['work_date', 'employee__last_name']

    def get_queryset(self):
        qs     = super().get_queryset()
        emp    = self.request.query_params.get('employee')
        month  = self.request.query_params.get('month')
        year   = self.request.query_params.get('year')
        dept   = self.request.query_params.get('department')

        if emp:
            qs = qs.filter(employee_id=emp)
        if month:
            qs = qs.filter(work_date__month=month)
        if year:
            qs = qs.filter(work_date__year=year)
        if dept:
            qs = qs.filter(employee__department_id=dept)
        return qs

    def paginate_queryset(self, queryset):
        # Отключаем пагинацию при запросе по месяцу (нужен весь список)
        if self.request.query_params.get('month'):
            return None
        return super().paginate_queryset(queryset)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Автоматически формирует табель за месяц для всех активных сотрудников.
        Тело запроса: { "month": 5, "year": 2026 }
        Уже существующие записи не перезаписываются.
        """
        try:
            target_month = int(request.data.get('month', date.today().month))
            target_year  = int(request.data.get('year',  date.today().year))
        except (TypeError, ValueError):
            return Response({'error': 'Неверный формат месяца/года.'}, status=400)

        days_in_month = calendar.monthrange(target_year, target_month)[1]
        employees     = Employee.objects.filter(status='active')

        # Одобренные отпуска, которые пересекаются с месяцем
        leave_days: set[tuple] = set()
        month_start = date(target_year, target_month, 1)
        month_end   = date(target_year, target_month, days_in_month)
        for leave in LeaveRequest.objects.filter(
            status='approved',
            start_date__lte=month_end,
            end_date__gte=month_start,
        ):
            cur = max(leave.start_date, month_start)
            end = min(leave.end_date, month_end)
            while cur <= end:
                leave_days.add((leave.employee_id, cur))
                cur += timedelta(days=1)

        created_count = 0
        for emp in employees:
            for day_num in range(1, days_in_month + 1):
                d       = date(target_year, target_month, day_num)
                weekday = d.weekday()   # 0=Пн … 6=Вс

                if weekday >= 5:
                    day_type, hw, ot = Timesheet.DAY_WEEKEND, 0.0, 0.0
                elif (emp.id, d) in leave_days:
                    day_type, hw, ot = Timesheet.DAY_VACATION, 0.0, 0.0
                else:
                    day_type, hw, ot = Timesheet.DAY_WORK, 8.0, 0.0

                _, created = Timesheet.objects.get_or_create(
                    employee=emp,
                    work_date=d,
                    defaults={'day_type': day_type, 'hours_worked': hw, 'overtime_hours': ot},
                )
                if created:
                    created_count += 1

        return Response({
            'created': created_count,
            'month':   target_month,
            'year':    target_year,
            'message': f'Сформировано {created_count} новых записей.',
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Сводка по месяцу: итого часов по сотрудникам."""
        month = int(request.query_params.get('month', date.today().month))
        year  = int(request.query_params.get('year',  date.today().year))
        dept  = request.query_params.get('department')

        qs = Timesheet.objects.filter(work_date__month=month, work_date__year=year)
        if dept:
            qs = qs.filter(employee__department_id=dept)

        from django.db.models import Sum
        rows = (
            qs.values('employee__id', 'employee__last_name', 'employee__first_name',
                      'employee__department__name')
              .annotate(
                  total_hours    = Sum('hours_worked'),
                  total_overtime = Sum('overtime_hours'),
              )
              .order_by('employee__last_name')
        )
        return Response(list(rows))
