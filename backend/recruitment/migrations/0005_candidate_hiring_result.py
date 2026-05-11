from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0004_vacancy_public_fields_questionnaire'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='hiring_result',
            field=models.BooleanField(blank=True, null=True, verbose_name='Результат найма'),
        ),
    ]
