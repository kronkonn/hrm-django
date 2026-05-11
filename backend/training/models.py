from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    CATEGORY_CHOICES = [
        ('mandatory',    'Обязательный'),
        ('development',  'Развивающий'),
        ('technical',    'Технический'),
    ]
    STATUS_CHOICES = [
        ('active',   'Активный'),
        ('archived', 'Архив'),
    ]
    title          = models.CharField('Название', max_length=200)
    description    = models.TextField('Описание', blank=True)
    category       = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES, default='mandatory')
    duration_hours = models.PositiveIntegerField('Длительность (часов)', default=1)
    deadline       = models.DateField('Дедлайн', null=True, blank=True)
    status         = models.CharField('Статус', max_length=10, choices=STATUS_CHOICES, default='active')
    lessons        = models.JSONField('Уроки', default=list, blank=True)
    created_by     = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_courses', verbose_name='Создан кем',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering            = ['-created_at']

    def __str__(self):
        return self.title


class CourseAssignment(models.Model):
    STATUS_CHOICES = [
        ('assigned',    'Назначен'),
        ('in_progress', 'В процессе'),
        ('completed',   'Завершён'),
        ('overdue',     'Просрочен'),
    ]
    course       = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments', verbose_name='Курс')
    employee     = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='course_assignments', verbose_name='Сотрудник',
    )
    status             = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='assigned')
    assigned_at        = models.DateTimeField('Дата назначения', auto_now_add=True)
    completed_at       = models.DateTimeField('Дата завершения', null=True, blank=True)
    progress           = models.PositiveIntegerField('Прогресс (%)', default=0)
    completed_lessons  = models.JSONField('Пройденные уроки', default=list, blank=True)

    class Meta:
        verbose_name        = 'Назначение курса'
        verbose_name_plural = 'Назначения курсов'
        ordering            = ['-assigned_at']
        unique_together     = ('course', 'employee')

    def __str__(self):
        return f'{self.employee} — {self.course}'


class Certificate(models.Model):
    employee           = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='certificates', verbose_name='Сотрудник',
    )
    course             = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates', verbose_name='Курс')
    issued_at          = models.DateField('Дата выдачи')
    certificate_number = models.CharField('Номер сертификата', max_length=50, unique=True)

    class Meta:
        verbose_name        = 'Сертификат'
        verbose_name_plural = 'Сертификаты'
        ordering            = ['-issued_at']
        unique_together     = ('employee', 'course')

    def __str__(self):
        return f'{self.certificate_number} — {self.employee}'
