import django, os, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrm.settings')
django.setup()

from analytics.models import AttritionPrediction, Anomaly, EmployeeCluster
from employees.models import Employee
from django.db.models import Avg
from datetime import date

today = date.today()

def full_name(emp):
    if not emp: return None
    parts = [emp.last_name, emp.first_name]
    if emp.middle_name: parts.append(emp.middle_name[:1] + '.')
    return ' '.join(p for p in parts if p)

def initials(emp):
    if not emp: return ''
    result = emp.last_name or ''
    if emp.first_name: result += ' ' + emp.first_name[0] + '.'
    if emp.middle_name: result += emp.middle_name[0] + '.'
    return result.strip()

avg_ot = Employee.objects.filter(status='active').aggregate(v=Avg('overtime_hours'))['v'] or 0

print("=== High risk ===")
for pred in AttritionPrediction.objects.filter(risk_label='high').select_related('employee', 'employee__department'):
    emp = pred.employee
    print(f"  {initials(emp)}: risk={pred.risk_score*100:.1f}%  ot={emp.overtime_hours}  hf={emp.hours_fulfillment:.1f}%  awards={emp.awards_last_year}  daw={emp.days_since_last_award}")
    print(f"  Top factors: {[f['feature'] for f in (pred.top_factors or [])[:4]]}")

print("\n=== Medium risk ===")
for pred in AttritionPrediction.objects.filter(risk_label='medium').select_related('employee'):
    emp = pred.employee
    top3 = [f.get('feature') for f in (pred.top_factors or [])[:3]]
    print(f"  {initials(emp)}: risk={pred.risk_score*100:.1f}%  top3={top3}")

print("\n=== Anomalies ===")
for a in Anomaly.objects.filter(is_resolved=False).select_related('employee'):
    print(f"  {initials(a.employee) if a.employee else 'sys'}: {a.metric}  val={a.value:.1f}  exp={a.expected_value}  score={a.anomaly_score:.3f}")
    print(f"  desc: {a.description}")

print("\n=== Clusters (risk) ===")
for ec in EmployeeCluster.objects.filter(cluster_label__icontains='риск').select_related('employee'):
    print(f"  {initials(ec.employee)}: cluster={ec.cluster_label}")

print(f"\navg_ot across company: {avg_ot:.1f}h")
