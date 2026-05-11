from django.db import models
from employees.models import Employee


class AttritionPrediction(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='attrition_prediction')
    risk_score = models.FloatField(default=0.0, help_text='0.0 – 1.0')
    risk_label = models.CharField(max_length=10, default='low', help_text='low/medium/high')
    top_factors = models.JSONField(default=list, help_text='[{"feature": "...", "value": 0.5}, ...]')
    predicted_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Прогноз увольнения'
        verbose_name_plural = 'Прогнозы увольнений'
        ordering = ['-risk_score']

    def __str__(self):
        return f'{self.employee} — {self.risk_label} ({self.risk_score:.2f})'

    def save(self, *args, **kwargs):
        if self.risk_score >= 0.65:
            self.risk_label = 'high'
        elif self.risk_score >= 0.30:
            self.risk_label = 'medium'
        else:
            self.risk_label = 'low'
        super().save(*args, **kwargs)


class EmployeeCluster(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='cluster')
    cluster_id = models.IntegerField(default=0)
    x_tsne = models.FloatField(default=0.0)
    y_tsne = models.FloatField(default=0.0)
    cluster_label = models.CharField(max_length=50, blank=True)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Кластер сотрудника'
        verbose_name_plural = 'Кластеры сотрудников'

    def __str__(self):
        return f'{self.employee} — кластер {self.cluster_id}'


class Anomaly(models.Model):
    SEVERITY_CHOICES = [('low', 'Низкая'), ('medium', 'Средняя'), ('high', 'Высокая')]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='anomalies', null=True, blank=True)
    metric = models.CharField(max_length=100)
    value = models.FloatField()
    expected_value = models.FloatField(null=True, blank=True)
    anomaly_score = models.FloatField(default=0.0)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField(blank=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Аномалия'
        verbose_name_plural = 'Аномалии'
        ordering = ['-detected_at']

    def __str__(self):
        return f'{self.metric} — {self.severity} @ {self.detected_at:%Y-%m-%d}'


class MetricForecast(models.Model):
    METRIC_CHOICES = [
        ('headcount', 'Численность персонала'),
        ('turnover', 'Текучесть кадров'),
        ('avg_salary', 'Средняя зарплата'),
        ('sick_days', 'Дни на больничном'),
        ('overtime', 'Сверхурочные часы'),
    ]

    metric = models.CharField(max_length=50, choices=METRIC_CHOICES)
    period = models.DateField(help_text='Первый день прогнозируемого периода')
    actual_value = models.FloatField(null=True, blank=True)
    forecast_value = models.FloatField()
    lower_bound = models.FloatField(null=True, blank=True)
    upper_bound = models.FloatField(null=True, blank=True)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Прогноз метрики'
        verbose_name_plural = 'Прогнозы метрик'
        unique_together = ['metric', 'period']
        ordering = ['metric', 'period']

    def __str__(self):
        return f'{self.metric} — {self.period}'
