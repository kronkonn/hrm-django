from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_DIRECTOR   = 'DIRECTOR'
    ROLE_HR_MANAGER = 'HR_MANAGER'
    ROLE_EMPLOYEE   = 'EMPLOYEE'
    ROLE_ADMIN      = 'ADMIN'

    ROLE_CHOICES = [
        (ROLE_DIRECTOR,   'Директор'),
        (ROLE_HR_MANAGER, 'HR-менеджер'),
        (ROLE_EMPLOYEE,   'Сотрудник'),
        (ROLE_ADMIN,      'Администратор'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EMPLOYEE)
    employee = models.OneToOneField(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='user_profile',
    )

    class Meta:
        verbose_name        = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'{self.user.username} ({self.role})'

    @property
    def is_director(self):   return self.role == self.ROLE_DIRECTOR
    @property
    def is_hr_manager(self): return self.role == self.ROLE_HR_MANAGER
    @property
    def is_employee(self):   return self.role == self.ROLE_EMPLOYEE
    @property
    def is_admin(self):      return self.role == self.ROLE_ADMIN
