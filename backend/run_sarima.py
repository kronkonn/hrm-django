import django, os, sys
sys.stdout.reconfigure(encoding='utf-8')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hrm.settings'
django.setup()

from datetime import date as _date
from analytics.models import MetricForecast
from analytics.ml.forecasting import build_real_history, run_sarima_forecast, _generate_synthetic_fallback

_SARIMA_METRICS = ['headcount', 'avg_salary', 'sick_days', 'overtime', 'turnover']
MetricForecast.objects.all().delete()

for metric in _SARIMA_METRICS:
    history = build_real_history(metric, months=24)
    if len(history) < 3:
        history = _generate_synthetic_fallback(metric, months=24)
    forecasts = run_sarima_forecast(metric, history, periods=3)
    for f in forecasts:
        period = _date.fromisoformat(f['period'])
        MetricForecast.objects.update_or_create(
            metric=metric,
            period=period,
            defaults={
                'forecast_value': f['forecast_value'],
                'lower_bound':    f.get('lower_bound'),
                'upper_bound':    f.get('upper_bound'),
            },
        )
    vals = [f['forecast_value'] for f in forecasts]
    print(f'{metric}: {vals}')

print('Готово!')
