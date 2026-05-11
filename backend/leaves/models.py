from django.db import models
from employees.models import Employee


class LeaveRequest(models.Model):
    TYPE_CHOICES = [
        ('annual', 'Ежегодный'),
        ('sick', 'Больничный'),
        ('unpaid', 'Без сохранения зарплаты'),
        ('maternity', 'Декретный'),
        ('study', 'Учебный'),
    ]
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрен'),
        ('rejected', 'Отклонён'),
        ('cancelled', 'Отменён'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='annual')
    start_date = models.DateField()
    end_date = models.DateField()
    days_count = models.PositiveIntegerField(default=1)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заявка на отпуск'
        verbose_name_plural = 'Заявки на отпуск'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.employee} — {self.leave_type} ({self.start_date} – {self.end_date})'

    def save(self, *args, **kwargs):
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.days_count = delta.days + 1
        super().save(*args, **kwargs)


class SickLeaveDetails(models.Model):
    leave_request = models.OneToOneField(
        LeaveRequest, on_delete=models.CASCADE, related_name='sick_details'
    )
    sick_leave_number = models.CharField(max_length=12, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    close_date = models.DateField(null=True, blank=True)
    medical_institution = models.CharField(max_length=255, blank=True)
    diagnosis_code = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Данные больничного листа'
        verbose_name_plural = 'Данные больничных листов'

    def __str__(self):
        return f'ЭЛН {self.sick_leave_number or "—"} ({self.leave_request})'
