"""
SARIMA-прогнозирование метрик персонала.
Прогноз на 3 месяца вперёд, доверительный интервал 95% (alpha=0.05).
История берётся из реальных данных БД (Timesheet, Employee).
"""
import numpy as np
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


def _daterange_months(start: date, n: int) -> list:
    result = []
    year, month = start.year, start.month
    for _ in range(n):
        result.append(date(year, month, 1))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return result


def _fill_zeros(history: list) -> list:
    """Заменяет нули средним соседних ненулевых точек (линейная интерполяция)."""
    if not history:
        return history
    dates = [d for d, _ in history]
    vals = list(float(v) for _, v in history)

    for i, v in enumerate(vals):
        if v == 0.0:
            left  = next((vals[j] for j in range(i - 1, -1, -1) if vals[j] != 0.0), None)
            right = next((vals[j] for j in range(i + 1, len(vals)) if vals[j] != 0.0), None)
            if left is not None and right is not None:
                vals[i] = (left + right) / 2.0
            elif left is not None:
                vals[i] = left
            elif right is not None:
                vals[i] = right

    return list(zip(dates, [round(v, 2) for v in vals]))


def _smooth_outliers(history: list) -> list:
    """Скользящее среднее (окно 3) если max/min > 10× — сглаживает аномальные выбросы."""
    if len(history) < 3:
        return history
    vals = [v for _, v in history]
    nonzero = [v for v in vals if v > 0]
    if not nonzero:
        return history
    if max(nonzero) / min(nonzero) > 10:
        smoothed = []
        for i in range(len(vals)):
            window = vals[max(0, i - 1): i + 2]
            smoothed.append(round(sum(window) / len(window), 2))
        return list(zip([d for d, _ in history], smoothed))
    return history


def build_real_history(metric: str, months: int = 18) -> list:
    """
    Строит список (date, value) из реальных данных БД.
    Метрики: headcount, avg_salary, sick_days, overtime, turnover.
    Применяет заполнение нулей и сглаживание выбросов перед возвратом.
    """
    import calendar
    from django.db.models import Avg, Sum

    today = date.today()
    history = []

    for i in range(months, 0, -1):
        year  = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year  -= 1

        d = date(year, month, 1)

        try:
            if metric == 'headcount':
                from employees.models import Employee
                last_day = calendar.monthrange(year, month)[1]
                val = float(Employee.objects.filter(
                    hire_date__lte=date(year, month, last_day),
                ).count())

            elif metric == 'avg_salary':
                from employees.models import Employee
                result = Employee.objects.filter(
                    status='active', hire_date__lte=date(year, month, calendar.monthrange(year, month)[1])
                ).aggregate(avg=Avg('salary'))
                val = float(result['avg'] or 0)

            elif metric == 'sick_days':
                from timesheets.models import Timesheet
                val = float(Timesheet.objects.filter(
                    day_type='SICK', work_date__year=year, work_date__month=month,
                ).count())

            elif metric == 'overtime':
                from timesheets.models import Timesheet
                result = Timesheet.objects.filter(
                    day_type='WORK', work_date__year=year, work_date__month=month,
                ).aggregate(total=Sum('overtime_hours'))
                val = float(result['total'] or 0)

            else:  # turnover — уволенные / все нанятые до конца месяца × 100
                last_day = calendar.monthrange(year, month)[1]
                month_end = date(year, month, last_day)
                from employees.models import Employee
                active_count     = float(Employee.objects.filter(
                    hire_date__lte=month_end, status='active',
                ).count())
                terminated_count = float(Employee.objects.filter(
                    hire_date__lte=month_end, status='inactive',
                ).count())
                total = active_count + terminated_count
                val = round((terminated_count / total * 100), 2) if total > 0 else 0.0

        except Exception as exc:
            logger.warning('[SARIMA] Ошибка при получении истории %s за %s/%s: %s', metric, month, year, exc)
            val = None

        if val is not None:
            history.append((d, round(val, 2)))

    # Заполняем нули интерполяцией, затем сглаживаем выбросы
    history = _fill_zeros(history)
    history = _smooth_outliers(history)
    return history


def _generate_synthetic_fallback(metric: str, months: int = 18) -> list:
    """Синтетическая история — только если реальные данные недоступны."""
    today = date.today()
    base, noise = {
        'headcount':  (28, 2),
        'turnover':   (35.0, 3.0),
        'avg_salary': (87000, 1000),
        'sick_days':  (12, 4),
        'overtime':   (25, 8),
    }.get(metric, (100, 10))

    history = []
    for i in range(months, 0, -1):
        year  = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year  -= 1
        d     = date(year, month, 1)
        trend = (months - i) * base * 0.003
        val   = base + np.random.randn() * noise + trend
        history.append((d, round(float(max(0.0, val)), 2)))
    return history


def run_sarima_forecast(metric: str, history: list, periods: int = 3) -> list:
    """
    Прогноз SARIMA на `periods` месяцев вперёд.
    Доверительный интервал: 95% (alpha=0.05).
    """
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        import warnings
        warnings.filterwarnings('ignore')

        if len(history) < 8:
            logger.warning('[SARIMA:%s] Мало данных (%d точек), используется линейный прогноз', metric, len(history))
            return _fallback_forecast(history, periods)

        values = [v for _, v in sorted(history)]
        hist_mean = sum(values) / len(values) if values else 1.0
        hist_std  = float(np.std(values)) if len(values) > 1 else 0.0

        # Вырожденный ряд (нулевая дисперсия) → линейный прогноз
        if hist_std < 1e-6:
            return _fallback_forecast(history, periods)

        if len(values) >= 24:
            model = SARIMAX(
                values,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
        else:
            model = SARIMAX(
                values,
                order=(1, 1, 1),
                seasonal_order=(0, 0, 0, 0),
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
        result        = model.fit(disp=False)
        forecast_obj  = result.get_forecast(steps=periods)
        fm_raw        = forecast_obj.predicted_mean
        ci_raw        = forecast_obj.conf_int(alpha=0.05)
        forecast_mean = np.array(fm_raw).flatten()
        conf_int      = np.array(ci_raw)

        aic = round(result.aic, 2)
        bic = round(result.bic, 2)
        print(
            f'[SARIMA:{metric}] n={len(values)} | AIC={aic} | BIC={bic} | '
            f'hist_mean={hist_mean:.1f} | '
            f'forecast=[{forecast_mean[0]:.2f}..{forecast_mean[-1]:.2f}]'
        )

        last_date = max(d for d, _ in history)
        forecast_dates = _daterange_months(
            date(last_date.year, last_date.month, 1) + timedelta(days=32),
            periods,
        )

        # Проверка разумности: прогноз не должен отличаться от среднего более чем в 5×
        hist_max = max(abs(v) for v in values) if values else 1.0
        if (any(abs(float(forecast_mean[i])) > hist_max * 100 for i in range(len(forecast_mean))) or
                any(abs(float(forecast_mean[i])) > hist_mean * 5 + hist_std * 3 for i in range(len(forecast_mean)))):
            logger.warning('[SARIMA:%s] Нестабильный прогноз (выброс), используется линейный', metric)
            return _fallback_forecast(history, periods)

        forecasts = []
        for i, d in enumerate(forecast_dates):
            fv    = max(0.0, float(forecast_mean[i]))
            lower = float(conf_int[i, 0])
            upper = float(conf_int[i, 1])
            if np.isnan(lower) or np.isinf(lower):
                lower = fv * 0.95
            if np.isnan(upper) or np.isinf(upper):
                upper = fv * 1.05
            lower = max(0.0, lower)
            forecasts.append({
                'period':         d.isoformat(),
                'forecast_value': round(fv, 2),
                'lower_bound':    round(lower, 2),
                'upper_bound':    round(upper, 2),
            })
        return forecasts

    except Exception as exc:
        logger.warning('[SARIMA:%s] Ошибка при подборе модели: %s', metric, exc)
        return _fallback_forecast(history, periods)


def _fallback_forecast(history: list, periods: int) -> list:
    """Линейный тренд + ±8% доверительный интервал."""
    if history:
        vals     = [v for _, v in history]
        last_val = vals[-1]
        trend    = (vals[-1] - vals[0]) / max(len(vals), 1) if len(vals) >= 2 else 0.0
    else:
        last_val, trend = 100.0, 1.0

    last_date = history[-1][0] if history else date.today()
    forecast_dates = _daterange_months(
        date(last_date.year, last_date.month, 1) + timedelta(days=32),
        periods,
    )

    forecasts = []
    for i, d in enumerate(forecast_dates, 1):
        fv = max(0.0, last_val + trend * i)
        forecasts.append({
            'period':         d.isoformat(),
            'forecast_value': round(float(fv), 2),
            'lower_bound':    round(float(fv * 0.92), 2),
            'upper_bound':    round(float(fv * 1.08), 2),
        })
    return forecasts
