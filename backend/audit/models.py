from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Создание'),
        ('UPDATE', 'Изменение'),
        ('DELETE', 'Удаление'),
        ('LOGIN',  'Вход в систему'),
        ('LOGOUT', 'Выход из системы'),
        ('VIEW',   'Просмотр'),
    ]

    user        = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')
    action      = models.CharField(max_length=10, choices=ACTION_CHOICES, db_index=True)
    model_name  = models.CharField(max_length=100, blank=True, db_index=True)
    object_id   = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes     = models.JSONField(null=True, blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True, db_index=True)
    details     = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name        = 'Запись аудита'
        verbose_name_plural = 'Журнал аудита'

    def __str__(self):
        user_str = self.user.username if self.user else 'аноним'
        return f'[{self.timestamp:%Y-%m-%d %H:%M}] {self.action} | {user_str} | {self.model_name}'
