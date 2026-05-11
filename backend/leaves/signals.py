from datetime import date

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='leaves.LeaveRequest')
def sync_employee_status(sender, instance, **kwargs):
    """Синхронизирует employee.status при сохранении LeaveRequest."""
    if instance.status != 'approved':
        # Заявка отклонена/отменена — если сотрудник был отмечен «в отпуске»
        # именно по этой заявке, возвращаем 'active'
        _maybe_restore_active(instance.employee, exclude_id=instance.pk)
        return

    today = date.today()
    emp = instance.employee

    if instance.start_date <= today <= instance.end_date:
        if emp.status != 'on_leave':
            # avoid recursive signal
            from employees.models import Employee
            Employee.objects.filter(pk=emp.pk).update(status='on_leave')
    elif today > instance.end_date:
        # Одобренный отпуск уже завершился — проверяем, есть ли другой активный
        _maybe_restore_active(emp, exclude_id=instance.pk)


def _maybe_restore_active(employee, exclude_id=None):
    """Возвращает статус 'active', если нет другого активного одобренного отпуска."""
    from employees.models import Employee
    today = date.today()
    qs = employee.leave_requests.filter(
        status='approved',
        start_date__lte=today,
        end_date__gte=today,
    )
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    if not qs.exists() and employee.status == 'on_leave':
        Employee.objects.filter(pk=employee.pk).update(status='active')
