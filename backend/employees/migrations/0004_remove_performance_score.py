from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_remove_satisfaction_score'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='performance_score',
        ),
    ]
