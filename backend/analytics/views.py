from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.permissions import IsDirector, IsHROrDirector
from .models import AttritionPrediction, EmployeeCluster, Anomaly, MetricForecast
from .serializers import (
    AttritionPredictionSerializer, EmployeeClusterSerializer,
    AnomalySerializer, MetricForecastSerializer,
)


class AttritionPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AttritionPrediction.objects.select_related('employee', 'employee__department').all()
    serializer_class = AttritionPredictionSerializer
    permission_classes = [IsDirector]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-risk_score']

    def get_queryset(self):
        qs = super().get_queryset()
        label = self.request.query_params.get('risk_label')
        if label:
            qs = qs.filter(risk_label=label)
        return qs


class EmployeeClusterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmployeeCluster.objects.select_related('employee', 'employee__department').all()
    serializer_class = EmployeeClusterSerializer
    permission_classes = [IsDirector]
    filter_backends = [filters.OrderingFilter]
    ordering = ['cluster_id']

    def get_queryset(self):
        qs = super().get_queryset()
        cid = self.request.query_params.get('cluster_id')
        if cid is not None:
            qs = qs.filter(cluster_id=cid)
        return qs


class AnomalyViewSet(viewsets.ModelViewSet):
    queryset = Anomaly.objects.select_related('employee').all()
    serializer_class = AnomalySerializer
    permission_classes = [IsDirector]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-detected_at']

    def get_queryset(self):
        qs = super().get_queryset()
        resolved = self.request.query_params.get('resolved')
        severity = self.request.query_params.get('severity')
        if resolved is not None:
            qs = qs.filter(is_resolved=(resolved.lower() == 'true'))
        if severity:
            qs = qs.filter(severity=severity)
        return qs


class MetricForecastViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MetricForecast.objects.all()
    serializer_class = MetricForecastSerializer
    permission_classes = [IsDirector]
    filter_backends = [filters.OrderingFilter]
    ordering = ['metric', 'period']

    def get_queryset(self):
        qs = super().get_queryset()
        metric = self.request.query_params.get('metric')
        if metric:
            qs = qs.filter(metric=metric)
        return qs


@api_view(['POST'])
@permission_classes([IsDirector])
def run_analytics(request):
    """Запускает все ML-модели и сохраняет результаты."""
    from datetime import date as _date
    from employees.models import Employee
    from .ml.attrition import run_attrition_model
    from .ml.clustering import run_clustering
    from .ml.anomaly import run_anomaly_detection
    from .ml.forecasting import run_sarima_forecast, build_real_history, _generate_synthetic_fallback

    employees = list(Employee.objects.filter(status='active').select_related('department'))
    if not employees:
        return Response({'error': 'Нет активных сотрудников'}, status=400)

    print(f'[Analytics] Запуск анализа: {len(employees)} активных сотрудников')

    # 1. Прогноз увольнения (XGBoost на Employee + Timesheet + LeaveRequest)
    attrition_results = run_attrition_model(employees)
    for emp in employees:
        data = attrition_results.get(emp.id, {'risk_score': 0.0, 'top_factors': []})
        rs = data['risk_score']
        rl = 'high' if rs >= 0.65 else 'medium' if rs >= 0.30 else 'low'
        AttritionPrediction.objects.update_or_create(
            employee=emp,
            defaults={'risk_score': rs, 'risk_label': rl, 'top_factors': data['top_factors']},
        )

    # 2. Кластеризация (K-Means с автовыбором k по силуэту 3–8)
    cluster_results = run_clustering(employees)
    for emp in employees:
        data = cluster_results.get(emp.id, {'cluster_id': 0, 'x_tsne': 0.0, 'y_tsne': 0.0, 'cluster_label': ''})
        EmployeeCluster.objects.update_or_create(
            employee=emp,
            defaults=data,
        )

    # 3. Аномалии (Isolation Forest, contamination=0.05, правила mean±2σ)
    Anomaly.objects.filter(is_resolved=False).delete()
    anomaly_results = run_anomaly_detection(employees)
    for a in anomaly_results:
        emp_id = a.pop('employee_id', None)
        emp    = next((e for e in employees if e.id == emp_id), None)
        if emp:
            Anomaly.objects.create(employee=emp, **a)

    # 4. Прогнозы SARIMA — 3 месяца, 95% ДИ, история из реальных данных БД
    _SARIMA_METRICS = ['headcount', 'avg_salary', 'sick_days', 'overtime', 'turnover']
    MetricForecast.objects.all().delete()
    forecast_count = 0
    for metric in _SARIMA_METRICS:
        history = build_real_history(metric, months=24)
        # Для метрик без данных в БД — синтетическая история
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
            forecast_count += 1

    print(
        f'[Analytics] Готово: attrition={len(attrition_results)}, '
        f'clusters={len(cluster_results)}, anomalies={len(anomaly_results)}, '
        f'forecasts={forecast_count}'
    )

    return Response({
        'attrition_count': len(attrition_results),
        'clusters_count':  len(cluster_results),
        'anomalies_count': len(anomaly_results),
        'forecasts_count': forecast_count,
    })


@api_view(['GET'])
@permission_classes([IsDirector])
def get_recommendations(request):
    """Генерирует подробные рекомендации на основе результатов всех ML-моделей."""
    from datetime import date
    from django.db.models import Avg
    from employees.models import Employee

    today = date.today()
    recs = []

    def full_name(emp):
        if not emp:
            return None
        parts = [emp.last_name, emp.first_name]
        if emp.middle_name:
            parts.append(emp.middle_name[:1] + '.')
        return ' '.join(p for p in parts if p) or emp.first_name

    def initials(emp):
        """Фамилия И.О."""
        if not emp:
            return ''
        result = emp.last_name or ''
        if emp.first_name:
            result += ' ' + emp.first_name[0] + '.'
        if emp.middle_name:
            result += emp.middle_name[0] + '.'
        return result.strip()

    # Среднее overtime_hours по всем активным для сравнения
    avg_ot = Employee.objects.filter(status='active').aggregate(v=Avg('overtime_hours'))['v'] or 0

    # ── 1. XGBoost — высокий риск увольнения ────────────────────────────────
    for pred in AttritionPrediction.objects.filter(risk_label='high').select_related('employee', 'employee__department'):
        emp = pred.employee
        factors = pred.top_factors or []

        # Собираем ключевые факторы из top_factors.
        # Правило: overtime_hours > 10 и hours_fulfillment < 85% — взаимоисключающие факторы.
        # Если переработки — работает БОЛЬШЕ нормы, hf не показываем.
        # Если нехватка часов — работает МЕНЬШЕ нормы, overtime не показываем.
        factor_lines = []
        work_metric_shown = None   # 'ot' или 'hf' — чтобы не показывать оба одновременно
        for f in factors[:4]:
            feat = f.get('feature', '')
            direction = f.get('direction', '')
            if feat == 'overtime_hours' and direction == 'up' and emp.overtime_hours > 10:
                if work_metric_shown is None:
                    factor_lines.append(f"переработки {emp.overtime_hours:.0f}ч/мес (норма 0–8ч)")
                    work_metric_shown = 'ot'
            elif feat == 'hours_fulfillment' and direction == 'up' and work_metric_shown != 'ot':
                hf = emp.hours_fulfillment
                if hf < 85:
                    factor_lines.append(f"выполнение нормы часов {hf:.0f}%")
                    work_metric_shown = 'hf'
            elif feat == 'days_since_last_award' and direction == 'up':
                factor_lines.append(f"без наград {emp.days_since_last_award} дней")
            elif feat == 'awards_last_year' and direction == 'up':
                factor_lines.append(f"наград за год: {emp.awards_last_year}")
            elif feat == 'num_companies_worked' and direction == 'up':
                factor_lines.append(f"работодателей в прошлом: {emp.num_companies_worked}")
            elif feat == 'years_at_company' and direction == 'up':
                factor_lines.append(f"лет в компании: {emp.years_at_company}")
            elif feat == 'salary' and direction == 'up':
                factor_lines.append(f"зарплата {int(emp.salary):,} ₽".replace(',', ' '))

        reason_parts = f"Сотрудник {initials(emp)}: " + (
            ', '.join(factor_lines) if factor_lines else 'несколько факторов риска'
        ) + f". XGBoost оценивает вероятность увольнения в {pred.risk_score * 100:.0f}%."

        dept_name = emp.department.name if emp.department else 'отдел'
        recs.append({
            'type': 'attrition', 'severity': 'critical',
            'title': f'Высокий риск увольнения — {initials(emp)}',
            'reason': reason_parts,
            'action': (
                f'Проведите личную беседу в течение 7 дней. '
                f'Рассмотрите снижение нагрузки, внеплановое премирование '
                f'или карьерный разговор. Отдел: {dept_name}.'
            ),
            'employee_id': pred.employee_id,
            'employee_name': full_name(emp),
        })

    # ── 2. XGBoost — средний риск с критичными факторами ────────────────────
    for pred in AttritionPrediction.objects.filter(risk_label='medium').select_related('employee', 'employee__department'):
        emp = pred.employee
        factors = pred.top_factors or []
        top3_feats = [f.get('feature') for f in factors[:3]]

        # Правило взаимоисключения: overtime > 10 → работает БОЛЬШЕ нормы (hf не может быть < 85)
        # hf < 85 → работает МЕНЬШЕ нормы (overtime не может быть > 10)
        has_ot    = (emp.overtime_hours > 10 and
                     any(f.get('feature') == 'overtime_hours' and f.get('direction') == 'up' for f in factors[:3]))
        has_award = any(f.get('feature') == 'days_since_last_award' and f.get('direction') == 'up' for f in factors[:3])
        has_hf    = (emp.hours_fulfillment < 85 and not has_ot and
                     any(f.get('feature') == 'hours_fulfillment' and f.get('direction') == 'up' for f in factors[:3]))
        dept_name  = emp.department.name if emp.department else 'отделе'

        if has_ot:
            ratio = emp.overtime_hours / avg_ot if avg_ot else 0
            recs.append({
                'type': 'attrition', 'severity': 'warning',
                'title': f'Повышенные переработки — {initials(emp)}',
                'reason': (
                    f'{initials(emp)} работает сверхурочно {emp.overtime_hours:.0f}ч/мес'
                    + (f' — в {ratio:.1f}× выше среднего ({avg_ot:.0f}ч)' if avg_ot > 0 else '')
                    + f'. Риск-балл XGBoost: {pred.risk_score * 100:.0f}%.'
                ),
                'action': (
                    f'Проверьте загрузку в отделе «{dept_name}». '
                    f'Перераспределите задачи или добавьте ресурс. '
                    f'Проведите разговор о балансе нагрузки.'
                ),
                'employee_id': pred.employee_id,
                'employee_name': full_name(emp),
            })
        elif has_award:
            recs.append({
                'type': 'attrition', 'severity': 'warning',
                'title': f'Давно без признания — {initials(emp)}',
                'reason': (
                    f'{initials(emp)} не получал(а) наград {emp.days_since_last_award} дней'
                    f' (наград за год: {emp.awards_last_year}).'
                    f' Риск-балл XGBoost: {pred.risk_score * 100:.0f}%.'
                ),
                'action': (
                    f'Рассмотрите поощрение или публичную благодарность в ближайший месяц. '
                    f'Отдел: {dept_name}.'
                ),
                'employee_id': pred.employee_id,
                'employee_name': full_name(emp),
            })
        elif has_hf:
            hf = emp.hours_fulfillment
            recs.append({
                'type': 'attrition', 'severity': 'warning',
                'title': f'Низкое выполнение нормы часов — {initials(emp)}',
                'reason': (
                    f'{initials(emp)} отрабатывает {hf:.0f}% нормы рабочих часов за последние 30 дней.'
                    f' Риск-балл XGBoost: {pred.risk_score * 100:.0f}%.'
                ),
                'action': (
                    f'Выясните причину сниженной явки: возможны личные обстоятельства или '
                    f'скрытый конфликт. Отдел: {dept_name}.'
                ),
                'employee_id': pred.employee_id,
                'employee_name': full_name(emp),
            })

    # ── 3. Isolation Forest — нерешённые аномалии ───────────────────────────
    METRIC_RU = {
        'overtime_hours':    'сверхурочные часы',
        'hours_fulfillment': 'выполнение нормы часов',
        'salary':            'зарплата',
        'sick_days':         'больничные дни',
    }
    for anomaly in Anomaly.objects.filter(is_resolved=False).select_related('employee', 'employee__department'):
        emp   = anomaly.employee
        name  = initials(emp) if emp else 'Системная аномалия'
        fname = full_name(emp) if emp else None
        metric_ru = METRIC_RU.get(anomaly.metric, anomaly.metric)
        dept_name = emp.department.name if emp and emp.department else 'отделе'

        # Формируем фразу о конкретном значении
        val_str = ''
        if anomaly.value is not None and anomaly.expected_value is not None:
            val_str = (
                f'Фактическое значение: {anomaly.value:.1f}'
                f', ожидаемое: {anomaly.expected_value:.1f}.'
            )
        elif anomaly.value is not None:
            val_str = f'Значение показателя: {anomaly.value:.1f}.'

        recs.append({
            'type': 'anomaly', 'severity': 'warning',
            'title': f'Аномалия: {metric_ru} — {name}',
            'reason': (
                f'{anomaly.description} '
                f'{val_str} '
                f'Isolation Forest: anomaly score {anomaly.anomaly_score:.3f}.'
            ).strip(),
            'action': (
                f'Проверьте причину отклонения в отделе «{dept_name}». '
                f'При необходимости скорректируйте условия труда или нагрузку.'
            ),
            'employee_id': anomaly.employee_id,
            'employee_name': fname,
        })

    # ── 4. K-Means — кластер риска ───────────────────────────────────────────
    # Учитываем только сотрудников с risk_score >= 0.30, чтобы не смешивать
    # «формальный» кластер риска с реально невысоким риском
    _risk_emp_ids = set(
        AttritionPrediction.objects.filter(risk_score__gte=0.30).values_list('employee_id', flat=True)
    )
    risk_clusters = EmployeeCluster.objects.filter(cluster_label__icontains='риск').select_related('employee', 'employee__department')
    valid_clusters = [ec for ec in risk_clusters if ec.employee_id in _risk_emp_ids]
    risk_count = len(valid_clusters)
    if risk_count > 0:
        dept_names = sorted(set(
            ec.employee.department.name
            for ec in valid_clusters
            if ec.employee and ec.employee.department
        ))
        dept_str = ', '.join(dept_names) if dept_names else 'различных отделах'
        severity  = 'warning' if risk_count >= 3 else 'info'
        # Строим характеристику кластера на основе реальных данных
        cluster_emps = [ec.employee for ec in valid_clusters if ec.employee]
        high_ot_count = sum(1 for e in cluster_emps if e.overtime_hours > 10)
        low_hf_count  = sum(1 for e in cluster_emps if e.hours_fulfillment < 85)
        if high_ot_count > 0:
            cluster_trait = f'высокие переработки у {high_ot_count} из {risk_count} сотрудников'
        elif low_hf_count > 0:
            cluster_trait = f'недовыполнение нормы часов у {low_hf_count} из {risk_count} сотрудников'
        else:
            cluster_trait = 'отсутствие признания, частая смена работодателей'
        recs.append({
            'type': 'cluster', 'severity': severity,
            'title': f'K-Means: группа риска — {risk_count} сотрудников',
            'reason': (
                f'K-Means кластеризация выявила {risk_count} сотрудника(-ов) с риском ≥ 30% '
                f'в кластере повышенного риска. Отделы: {dept_str}. '
                f'Характерные черты: {cluster_trait}.'
            ),
            'action': (
                f'Проведите анонимный опрос вовлечённости в отделах: {dept_str}. '
                f'Обсудите командную динамику с тимлидами.'
            ),
            'employee_id': None,
            'employee_name': None,
        })

    # ── 5. Обучение ───────────────────────────────────────────────────────────
    try:
        from training.models import CourseAssignment
        all_ids      = set(Employee.objects.filter(status='active').values_list('id', flat=True))
        assigned_ids = set(CourseAssignment.objects.values_list('employee_id', flat=True))
        unassigned   = len(all_ids - assigned_ids)
        if unassigned:
            recs.append({
                'type': 'training', 'severity': 'info',
                'title': f'Нет назначенных курсов — {unassigned} сотрудников',
                'reason': (
                    f'{unassigned} из {len(all_ids)} активных сотрудников '
                    f'не имеют ни одного назначенного курса обучения.'
                ),
                'action': (
                    f'Зайдите в модуль «Обучение» и назначьте обязательные курсы '
                    f'(например, «Основы ИБ») всем сотрудникам без программ.'
                ),
                'employee_id': None,
                'employee_name': None,
            })

        for a in CourseAssignment.objects.filter(status='overdue').select_related('employee', 'course', 'employee__department'):
            emp       = a.employee
            dept_name = emp.department.name if emp and emp.department else 'отделе'
            recs.append({
                'type': 'training', 'severity': 'warning',
                'title': f'Просроченный курс — {initials(emp)}',
                'reason': (
                    f'Курс «{a.course.title}» имеет статус "просрочен". '
                    f'Сотрудник {initials(emp)}, отдел: {dept_name}.'
                ),
                'action': (
                    f'Свяжитесь с {initials(emp)} и установите новый срок. '
                    f'Или переназначьте курс с обновлённым дедлайном.'
                ),
                'employee_id': a.employee_id,
                'employee_name': full_name(emp),
            })

        for a in CourseAssignment.objects.filter(
            status__in=['assigned', 'in_progress'],
            course__deadline__lt=today,
        ).select_related('employee', 'course', 'employee__department'):
            emp       = a.employee
            overdue_days = (today - a.course.deadline).days
            dept_name = emp.department.name if emp and emp.department else 'отделе'
            recs.append({
                'type': 'training', 'severity': 'warning',
                'title': f'Дедлайн прошёл — {initials(emp)}',
                'reason': (
                    f'Курс «{a.course.title}» не завершён. '
                    f'Дедлайн истёк {overdue_days} дн. назад. '
                    f'Статус: {a.status}. Отдел: {dept_name}.'
                ),
                'action': (
                    f'Выясните причину задержки у {initials(emp)}. '
                    f'Обновите дедлайн или переведите курс в статус "просрочен".'
                ),
                'employee_id': a.employee_id,
                'employee_name': full_name(emp),
            })
    except Exception:
        pass

    PRIORITY = {'critical': 0, 'warning': 1, 'info': 2}
    recs.sort(key=lambda x: PRIORITY.get(x['severity'], 3))
    return Response(recs)


@api_view(['GET'])
@permission_classes([IsDirector])
def department_clusters(request):
    from collections import Counter
    from employees.models import Employee

    CLUSTER_LABELS = {
        0: 'Высокая эффективность',
        1: 'Группа риска',
        2: 'Стабильные',
        3: 'Новички',
    }

    employees = list(
        Employee.objects.filter(status='active')
        .select_related('department', 'attrition_prediction', 'cluster')
    )

    dept_data = {}
    for emp in employees:
        dept = emp.department
        if not dept:
            continue
        did = dept.id
        if did not in dept_data:
            dept_data[did] = {'department_name': dept.name, 'entries': []}

        try:
            risk = emp.attrition_prediction.risk_score
        except Exception:
            risk = 0.0

        try:
            cid = emp.cluster.cluster_id
        except Exception:
            cid = 0

        dept_data[did]['entries'].append({
            'id': emp.id,
            'name': f'{emp.last_name} {emp.first_name}'.strip(),
            'risk_score': risk,
            'cluster_id': cid,
            'hours_fulfillment': emp.hours_fulfillment,
        })

    result = []
    for data in dept_data.values():
        entries = data['entries']
        n = len(entries)
        avg_risk = sum(e['risk_score'] for e in entries) / n if n else 0.0
        avg_hf   = sum(e['hours_fulfillment'] for e in entries) / n if n else 0.0
        cid_counts = Counter(e['cluster_id'] for e in entries)
        dom_cid    = cid_counts.most_common(1)[0][0]

        result.append({
            'department_name':       data['department_name'],
            'employee_count':        n,
            'avg_risk_score':        round(avg_risk * 100, 1),
            'avg_hours_fulfillment': round(avg_hf, 1),
            'dominant_cluster':      CLUSTER_LABELS.get(dom_cid, f'Кластер {dom_cid}'),
            'dominant_cluster_id':   dom_cid,
            'employees': [
                {'id': e['id'], 'name': e['name'], 'risk_score': round(e['risk_score'] * 100, 1)}
                for e in entries
            ],
        })

    result.sort(key=lambda x: -x['avg_risk_score'])
    return Response(result)


@api_view(['GET'])
@permission_classes([IsHROrDirector])
def dashboard_summary(request):
    from employees.models import Employee
    from leaves.models import LeaveRequest
    from recruitment.models import Vacancy, Candidate

    active_employees = Employee.objects.filter(status='active').count()
    pending_leaves = LeaveRequest.objects.filter(status='pending').count()
    open_vacancies = Vacancy.objects.filter(status='open').count()
    total_candidates = Candidate.objects.count()

    data = {
        'active_employees': active_employees,
        'pending_leaves': pending_leaves,
        'open_vacancies': open_vacancies,
        'total_candidates': total_candidates,
    }

    # Статистика аналитики — только для директора
    role = getattr(getattr(request.user, 'profile', None), 'role', None)
    if role == 'DIRECTOR':
        data['high_risk_employees'] = AttritionPrediction.objects.filter(risk_label='high').count()
        data['active_anomalies'] = Anomaly.objects.filter(is_resolved=False).count()

    return Response(data)
