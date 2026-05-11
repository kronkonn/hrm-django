from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leaves', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SickLeaveDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sick_leave_number', models.CharField(blank=True, max_length=12)),
                ('issue_date', models.DateField(blank=True, null=True)),
                ('close_date', models.DateField(blank=True, null=True)),
                ('medical_institution', models.CharField(blank=True, max_length=255)),
                ('diagnosis_code', models.CharField(blank=True, max_length=20)),
                ('leave_request', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sick_details',
                    to='leaves.leaverequest',
                )),
            ],
            options={
                'verbose_name': 'Данные больничного листа',
                'verbose_name_plural': 'Данные больничных листов',
            },
        ),
    ]
