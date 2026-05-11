from django.db import models
from hrm.encryption import EncryptedCharField, EncryptedDateField


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
        ordering = ['name']

    def __str__(self):
        return self.name


class Position(models.Model):
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='positions')
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        ordering = ['title']

    def __str__(self):
        return f'{self.title} ({self.department})'


class Employee(models.Model):
    GENDER_CHOICES = [('M', 'Мужской'), ('F', 'Женский')]
    STATUS_CHOICES = [('active', 'Активный'), ('inactive', 'Уволен'), ('on_leave', 'В отпуске')]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(unique=True)
    phone = EncryptedCharField(max_length=20, blank=True)    # ФЗ-152: шифруется AES-256
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    birth_date = EncryptedDateField(null=True, blank=True)  # ФЗ-152: шифруется AES-256
    hire_date = models.DateField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, related_name='employees')
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    photo = models.ImageField(upload_to='employees/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Дополнительные поля для ML-моделей
    overtime_hours = models.FloatField(default=0)
    distance_from_home = models.IntegerField(default=10)
    num_companies_worked = models.IntegerField(default=1)
    years_at_company = models.IntegerField(default=0)
    training_times_last_year = models.IntegerField(default=2)

    # Признаки поощрений
    awards_last_year = models.IntegerField(default=0, help_text='Количество награждений за последний год')
    days_since_last_award = models.IntegerField(default=365, help_text='Дней с последнего награждения')
    bonus_share = models.FloatField(default=0.10, help_text='Доля переменной части в доходе (0.0-1.0)')
    has_bonus_program = models.BooleanField(default=False, help_text='Участие в бонусной программе')

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(p for p in parts if p)

    @property
    def hours_fulfillment(self):
        """% выполнения нормы часов за последние 30 дней. Диапазон 0–150."""
        from datetime import date, timedelta
        from django.db.models import Sum
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        try:
            from timesheets.models import Timesheet
            result = Timesheet.objects.filter(
                employee=self, day_type='WORK',
                work_date__gte=thirty_days_ago, work_date__lte=today,
            ).aggregate(total=Sum('hours_worked'))
            actual_hours = float(result['total'] or 0)
            work_days = sum(
                1 for i in range(31)
                if (thirty_days_ago + timedelta(days=i)).weekday() < 5
            )
            expected = work_days * 8
            return round(min(150.0, (actual_hours / expected) * 100), 1) if expected else 100.0
        except Exception:
            return 100.0
