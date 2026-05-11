from django.db import models
from employees.models import Employee


class Timesheet(models.Model):
    DAY_WORK     = 'WORK'
    DAY_SICK     = 'SICK'
    DAY_VACATION = 'VACATION'
    DAY_HOLIDAY  = 'HOLIDAY'
    DAY_WEEKEND  = 'WEEKEND'
    DAY_REMOTE   = 'REMOTE'

    DAY_TYPE_CHOICES = [
        (DAY_WORK,     'Рабочий день'),
        (DAY_SICK,     'Больничный'),
        (DAY_VACATION, 'Отпуск'),
        (DAY_HOLIDAY,  'Праздник'),
        (DAY_WEEKEND,  'Выходной'),
        (DAY_REMOTE,   'Удалённо'),
    ]

    employee      = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='timesheets')
    work_date     = models.DateField(verbose_name='Дата')
    day_type      = models.CharField(max_length=10, choices=DAY_TYPE_CHOICES, default=DAY_WORK)
    hours_worked  = models.FloatField(default=0, verbose_name='Часов отработано')
    overtime_hours = models.FloatField(default=0, verbose_name='Часов сверхурочно')
    note          = models.CharField(max_length=255, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Запись табеля'
        verbose_name_plural = 'Табель рабочего времени'
        unique_together     = ['employee', 'work_date']
        ordering            = ['work_date', 'employee__last_name']

    def __str__(self):
        return f'{self.employee} — {self.work_date} ({self.day_type})'
