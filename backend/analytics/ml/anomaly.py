"""
Isolation Forest для выявления аномалий в показателях сотрудников.
contamination=0.05; типы определяются по правилу mean ± 2σ на реальных данных.
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)

_FEATURE_RU = {
    'salary':            'Зарплата',
    'overtime_hours':    'Сверхурочные часы',
    'hours_fulfillment': 'Выполнение нормы часов (%)',
    'sick_days_year':    'Больничных дней',
    'years_at_company':  'Стаж работы',
}


def _query_sick_days(emp_ids: list) -> dict:
    """Возвращает {emp_id: sick_days_count} за последний год из Timesheet."""
    from datetime import date, timedelta
    from django.db.models import Count
    from timesheets.models import Timesheet

    one_year_ago = date.today() - timedelta(days=365)
    return dict(
        Timesheet.objects
        .filter(employee_id__in=emp_ids, day_type='SICK', work_date__gte=one_year_ago)
        .values('employee_id')
        .annotate(cnt=Count('id'))
        .values_list('employee_id', 'cnt')
    )


def _classify_anomaly(X_raw_row: np.ndarray, means: np.ndarray,
                      stds: np.ndarray, col: dict):
    """
    Выбирает единственный тип аномалии — с наибольшим σ-отклонением.
    Возвращает (feature_name, raw_value, description) или None.
    Это предотвращает противоречие: переработки и нехватка нормы часов
    не могут быть аномалиями одновременно у одного сотрудника.
    """
    eps = 1e-9
    candidates = []

    v_ot = X_raw_row[col['overtime_hours']]
    m_ot = means[col['overtime_hours']]
    s_ot = max(stds[col['overtime_hours']], eps)
    if v_ot > m_ot + 2 * s_ot:
        candidates.append((
            (v_ot - m_ot) / s_ot,
            'overtime_hours', v_ot,
            f'Резкий рост переработок: {v_ot:.0f}ч/мес (среднее {m_ot:.0f}ч)',
        ))

    v_hf = X_raw_row[col['hours_fulfillment']]
    m_hf = means[col['hours_fulfillment']]
    s_hf = max(stds[col['hours_fulfillment']], eps)
    if v_hf < m_hf - 2 * s_hf:
        candidates.append((
            (m_hf - v_hf) / s_hf,
            'hours_fulfillment', v_hf,
            f'Низкое выполнение нормы часов: {v_hf:.0f}% (норма {m_hf:.0f}%)',
        ))

    v_sick = X_raw_row[col['sick_days_year']]
    m_sick = means[col['sick_days_year']]
    s_sick = max(stds[col['sick_days_year']], eps)
    if v_sick > m_sick + 2 * s_sick:
        candidates.append((
            (v_sick - m_sick) / s_sick,
            'sick_days_year', v_sick,
            f'Повышенная частота больничных: {v_sick:.0f} дней (норма {m_sick:.0f} дней)',
        ))

    if not candidates:
        return None
    # Единственная аномалия — с наибольшим σ-отклонением
    best = max(candidates, key=lambda x: x[0])
    return best[1], best[2], best[3]  # (feature, value, description)


def run_anomaly_detection(employees):
    """
    Isolation Forest с contamination=0.05.
    Признаки: salary, overtime_hours, hours_fulfillment, sick_days_year, years_at_company.
    Типы аномалий определяются по правилам mean ± 2σ на реальных данных из Timesheet.
    Выводит метрики в консоль Django.
    """
    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return _fallback_anomalies(employees)

    if len(employees) < 5:
        return _fallback_anomalies(employees)

    from datetime import date, timedelta
    from django.db.models import Sum
    from timesheets.models import Timesheet as _TS

    emp_ids     = [emp.id for emp in employees]
    sick_counts = _query_sick_days(emp_ids)

    # Bulk hours_fulfillment
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    work_hours_30 = dict(
        _TS.objects
        .filter(employee_id__in=emp_ids, day_type='WORK',
                work_date__gte=thirty_days_ago, work_date__lte=today)
        .values('employee_id')
        .annotate(total=Sum('hours_worked'))
        .values_list('employee_id', 'total')
    )
    weekdays_30 = sum(
        1 for i in range(31)
        if (thirty_days_ago + timedelta(days=i)).weekday() < 5
    )
    expected_30 = weekdays_30 * 8 or 1

    # Feature matrix
    feature_names = ['salary', 'overtime_hours', 'hours_fulfillment',
                     'sick_days_year', 'years_at_company']
    col = {n: i for i, n in enumerate(feature_names)}

    X_raw = np.array([[
        float(emp.salary),
        float(emp.overtime_hours),
        round(min(150.0, float(work_hours_30.get(emp.id) or 0) / expected_30 * 100), 1),
        float(sick_counts.get(emp.id, 0)),
        float(emp.years_at_company),
    ] for emp in employees])

    # Статистики для правил mean ± 2σ
    means = X_raw.mean(axis=0)
    stds  = X_raw.std(axis=0)

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    iso    = IsolationForest(contamination=0.05, random_state=42)
    preds  = iso.fit_predict(X_scaled)
    scores = iso.score_samples(X_scaled)

    n_anomalies = int((preds == -1).sum())
    print(
        f'[Anomaly IsolationForest] n_employees={len(employees)} | '
        f'contamination=0.05 | n_anomalies={n_anomalies} | '
        f'mean_overtime={means[col["overtime_hours"]]:.1f}h '
        f'(sd={stds[col["overtime_hours"]]:.1f}) | '
        f'mean_hf={means[col["hours_fulfillment"]]:.1f}% '
        f'(sd={stds[col["hours_fulfillment"]]:.1f}) | '
        f'mean_sick={means[col["sick_days_year"]]:.1f}d '
        f'(sd={stds[col["sick_days_year"]]:.1f})'
    )

    anomalies = []
    for i, emp_id in enumerate(emp_ids):
        if preds[i] != -1:
            continue

        anomaly_score = float(-scores[i])

        # Тип аномалии по правилам mean ± 2σ.
        # Если правило сработало — metric/value берём из правила (не из StandardScaler),
        # чтобы избежать несоответствия между metric='hours_fulfillment' и описанием 'переработки'.
        rule_result = _classify_anomaly(X_raw[i], means, stds, col)
        if rule_result:
            rule_feat, rule_val, rule_desc = rule_result
            metric      = rule_feat
            value       = rule_val
            expected    = float(means[col[rule_feat]])
            description = rule_desc
        else:
            # Нет правила — используем наиболее отклонившийся признак по StandardScaler
            most_deviant_idx = int(np.argmax(np.abs(X_scaled[i])))
            metric      = feature_names[most_deviant_idx]
            value       = float(X_raw[i, most_deviant_idx])
            expected    = float(means[most_deviant_idx])
            description = (
                f'Статистическая аномалия ({_FEATURE_RU.get(metric, metric)}): '
                f'{value:.1f} (среднее {expected:.1f})'
            )

        severity = 'high' if anomaly_score > 0.6 else 'medium'

        anomalies.append({
            'employee_id':   emp_id,
            'metric':        metric,
            'value':         round(value, 2),
            'expected_value': round(expected, 2),
            'anomaly_score': round(anomaly_score, 4),
            'severity':      severity,
            'description':   description,
        })
    return anomalies


def _fallback_anomalies(employees):
    anomalies = []
    for emp in employees:
        if emp.overtime_hours > 30:
            anomalies.append({
                'employee_id': emp.id,
                'metric': 'overtime_hours', 'value': float(emp.overtime_hours),
                'expected_value': 10.0, 'anomaly_score': 0.75, 'severity': 'high',
                'description': f'Резкий рост переработок: {emp.overtime_hours} ч.',
            })
        elif emp.hours_fulfillment < 60.0:
            hf = emp.hours_fulfillment
            anomalies.append({
                'employee_id': emp.id,
                'metric': 'hours_fulfillment', 'value': float(hf),
                'expected_value': 100.0, 'anomaly_score': 0.6, 'severity': 'medium',
                'description': f'Низкое выполнение нормы часов: {hf:.0f}%',
            })
    return anomalies
