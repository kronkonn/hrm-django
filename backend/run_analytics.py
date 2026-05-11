import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrm.settings')
django.setup()

from datetime import date as _date
from employees.models import Employee
from analytics.models import AttritionPrediction, EmployeeCluster, Anomaly
from analytics.ml.attrition import run_attrition_model
from analytics.ml.clustering import run_clustering
from analytics.ml.anomaly import run_anomaly_detection

employees = list(Employee.objects.filter(status='active').select_related('department'))
print(f'Active employees: {len(employees)}')

# Attrition
attrition_results = run_attrition_model(employees)
for emp in employees:
    data = attrition_results.get(emp.id, {'risk_score': 0.0, 'top_factors': []})
    rs = data['risk_score']
    rl = 'high' if rs >= 0.65 else 'medium' if rs >= 0.30 else 'low'
    AttritionPrediction.objects.update_or_create(
        employee=emp,
        defaults={'risk_score': rs, 'risk_label': rl, 'top_factors': data['top_factors']},
    )
print('Attrition done')

# Clustering
cluster_results = run_clustering(employees)
for emp in employees:
    data = cluster_results.get(emp.id, {'cluster_id': 0, 'x_tsne': 0.0, 'y_tsne': 0.0, 'cluster_label': ''})
    EmployeeCluster.objects.update_or_create(employee=emp, defaults=data)
print('Clustering done')

# Anomalies
Anomaly.objects.filter(is_resolved=False).delete()
anomaly_results = run_anomaly_detection(employees)
for a in anomaly_results:
    emp_id = a.pop('employee_id', None)
    emp = next((e for e in employees if e.id == emp_id), None)
    if emp:
        Anomaly.objects.create(employee=emp, **a)
print(f'Anomalies done: {len(anomaly_results)} detected')

# Verify
print('\n=== Results ===')
for pred in AttritionPrediction.objects.select_related('employee').order_by('-risk_score'):
    emp = pred.employee
    name = f'{emp.last_name} {emp.first_name[0]}.'
    factors = [(f['feature'], f.get('raw_value')) for f in (pred.top_factors or [])[:3]]
    print(f'  {name}: {pred.risk_label} {pred.risk_score*100:.1f}%  factors={factors}')
