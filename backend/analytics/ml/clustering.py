"""
K-Means кластеризация + t-SNE визуализация сотрудников.
Оптимальное число кластеров выбирается автоматически по коэффициенту силуэта (диапазон 3–8).
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


def _assign_cluster_labels(labels: np.ndarray, X_raw: np.ndarray) -> dict:
    """
    Динамически назначает семантические метки кластерам на основе характеристик центроидов.
    Столбцы X_raw: [salary, hours_fulfillment, overtime_hours, years_at_company, training]
    """
    cluster_ids = sorted(set(int(x) for x in labels))
    centroids = {cid: X_raw[labels == cid].mean(axis=0) for cid in cluster_ids}

    COL_HF   = 1  # hours_fulfillment
    COL_OT   = 2  # overtime_hours
    COL_YRS  = 3  # years_at_company

    # Определяем семантику каждого кластера
    max_perf  = max(cluster_ids, key=lambda c: centroids[c][COL_HF])
    max_ot    = max(cluster_ids, key=lambda c: centroids[c][COL_OT])
    min_years = min(cluster_ids, key=lambda c: centroids[c][COL_YRS])

    label_map: dict[int, str] = {}
    assigned: set[int] = set()

    # Группа риска — приоритет: наибольшие сверхурочные
    label_map[max_ot] = 'Группа риска'
    assigned.add(max_ot)

    # Новички — наименьший стаж (если не уже занят)
    if min_years not in assigned:
        label_map[min_years] = 'Новички'
        assigned.add(min_years)

    # Высокая эффективность — лучшая производительность (если не занят)
    if max_perf not in assigned:
        label_map[max_perf] = 'Высокая эффективность'
        assigned.add(max_perf)

    # Остальные → Стабильные
    for cid in cluster_ids:
        if cid not in assigned:
            label_map[cid] = 'Стабильные'

    return label_map


def run_clustering(employees):
    """
    Кластеризует сотрудников K-Means.
    Оптимальное k выбирается в диапазоне 3–8 по коэффициенту силуэта.
    Выводит метрики в консоль Django.
    """
    try:
        from sklearn.cluster import KMeans
        from sklearn.manifold import TSNE
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score
    except ImportError:
        return _fallback_clusters(employees)

    if len(employees) < 3:
        return _fallback_clusters(employees)

    ids = [emp.id for emp in employees]

    # Precompute hours_fulfillment in bulk (avoids N+1 queries)
    from datetime import date, timedelta
    from django.db.models import Sum
    from timesheets.models import Timesheet
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    work_hours_30 = dict(
        Timesheet.objects
        .filter(employee_id__in=ids, day_type='WORK',
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

    X_raw = np.array([[
        float(emp.salary),
        round(min(150.0, float(work_hours_30.get(emp.id) or 0) / expected_30 * 100), 1),
        float(emp.overtime_hours),
        float(emp.years_at_company),
        float(emp.training_times_last_year),
    ] for emp in employees])

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # Автовыбор числа кластеров по коэффициенту силуэта (диапазон 3–8)
    max_k = min(8, len(employees) - 1)
    min_k = min(3, max_k)

    best_k, best_score, scores_log = min_k, -1.0, {}
    for k in range(min_k, max_k + 1):
        km  = KMeans(n_clusters=k, random_state=42, n_init=10)
        lbs = km.fit_predict(X_scaled)
        if len(set(lbs)) < 2:
            continue
        sc = silhouette_score(X_scaled, lbs)
        scores_log[k] = round(sc, 4)
        if sc > best_score:
            best_k, best_score = k, sc

    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    label_map = _assign_cluster_labels(labels, X_raw)

    print(
        f'[Clustering KMeans] n_samples={len(employees)} | '
        f'optimal_k={best_k} | best_silhouette={best_score:.4f} | '
        f'silhouette_by_k={scores_log} | '
        f'labels={label_map}'
    )

    perplexity = min(30, max(5, len(employees) - 1))
    tsne   = TSNE(n_components=2, random_state=42, perplexity=perplexity)
    coords = tsne.fit_transform(X_scaled)

    results = {}
    for i, emp_id in enumerate(ids):
        cid = int(labels[i])
        results[emp_id] = {
            'cluster_id':    cid,
            'x_tsne':        round(float(coords[i, 0]), 4),
            'y_tsne':        round(float(coords[i, 1]), 4),
            'cluster_label': label_map.get(cid, f'Кластер {cid}'),
        }
    return results


def _fallback_clusters(employees):
    _LABELS = {0: 'Высокая эффективность', 1: 'Группа риска', 2: 'Стабильные', 3: 'Новички'}
    results = {}
    for i, emp in enumerate(employees):
        cid = i % 4
        results[emp.id] = {
            'cluster_id':    cid,
            'x_tsne':        round(float(cid * 5.0 + i * 0.1), 4),
            'y_tsne':        round(float(cid * 3.0 + i * 0.1), 4),
            'cluster_label': _LABELS.get(cid, f'Кластер {cid}'),
        }
    return results
