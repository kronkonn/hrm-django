"""
Миграция обновлена вручную:
  - work_date добавляется как NULL (без дефолта)
  - RunSQL копирует date -> work_date
  - RunSQL удаляет дубликаты, оставляя MIN(id) по (employee_id, work_date)
  - только потом создаётся уникальный индекс
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
        ('timesheets', '0001_initial'),
    ]

    operations = [
        # 1. Обновляем Meta-опции (без изменений в БД)
        migrations.AlterModelOptions(
            name='timesheet',
            options={
                'ordering': ['work_date', 'employee__last_name'],
                'verbose_name': 'Запись табеля',
                'verbose_name_plural': 'Табель рабочего времени',
            },
        ),

        # 2. Снимаем старый уникальный индекс (employee, date)
        migrations.AlterUniqueTogether(
            name='timesheet',
            unique_together=set(),
        ),

        # 3. Добавляем новые поля
        migrations.AddField(
            model_name='timesheet',
            name='day_type',
            field=models.CharField(
                choices=[
                    ('WORK',     'Рабочий день'),
                    ('SICK',     'Больничный'),
                    ('VACATION', 'Отпуск'),
                    ('HOLIDAY',  'Праздник'),
                    ('WEEKEND',  'Выходной'),
                    ('REMOTE',   'Удалённо'),
                ],
                default='WORK',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='timesheet',
            name='note',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='timesheet',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),

        # 4. Добавляем work_date как NULLABLE — без дефолта, чтобы не получить
        #    одну и ту же дату для всех строк и последующий конфликт уникальности.
        migrations.AddField(
            model_name='timesheet',
            name='work_date',
            field=models.DateField(null=True, verbose_name='Дата'),
        ),

        # 5. Копируем существующее поле date -> work_date (прямой SQL — надёжнее ORM в миграциях)
        migrations.RunSQL(
            sql='UPDATE timesheets_timesheet SET work_date = date',
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 6. Удаляем дубликаты по (employee_id, work_date),
        #    оставляем запись с наименьшим id для каждой пары.
        migrations.RunSQL(
            sql="""
                DELETE FROM timesheets_timesheet
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM timesheets_timesheet
                    GROUP BY employee_id, work_date
                )
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 7. Теперь work_date можно сделать обязательным
        migrations.AlterField(
            model_name='timesheet',
            name='work_date',
            field=models.DateField(verbose_name='Дата'),
        ),

        # 8. Обновляем verbose_name числовых полей
        migrations.AlterField(
            model_name='timesheet',
            name='hours_worked',
            field=models.FloatField(default=0, verbose_name='Часов отработано'),
        ),
        migrations.AlterField(
            model_name='timesheet',
            name='overtime_hours',
            field=models.FloatField(default=0, verbose_name='Часов сверхурочно'),
        ),

        # 9. Добавляем новый уникальный индекс — дубликатов уже нет
        migrations.AlterUniqueTogether(
            name='timesheet',
            unique_together={('employee', 'work_date')},
        ),

        # 10. Удаляем устаревшие поля старой модели
        migrations.RemoveField(model_name='timesheet', name='check_in'),
        migrations.RemoveField(model_name='timesheet', name='check_out'),
        migrations.RemoveField(model_name='timesheet', name='date'),
        migrations.RemoveField(model_name='timesheet', name='notes'),
        migrations.RemoveField(model_name='timesheet', name='status'),
    ]
