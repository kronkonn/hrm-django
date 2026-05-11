from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0002_candidate_ai_comment_candidate_ai_score_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacancy',
            name='required_skills',
            field=models.JSONField(blank=True, default=list, verbose_name='Требуемые навыки'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='experience_years',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Опыт (лет)'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='salary_from',
            field=models.IntegerField(blank=True, null=True, verbose_name='Зарплата от'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='salary_to',
            field=models.IntegerField(blank=True, null=True, verbose_name='Зарплата до'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='responsibilities',
            field=models.TextField(blank=True, verbose_name='Обязанности'),
        ),
        migrations.AddField(
            model_name='vacancy',
            name='conditions',
            field=models.TextField(blank=True, verbose_name='Условия работы'),
        ),
        migrations.AlterField(
            model_name='vacancy',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='vacancy',
            name='employment_type',
            field=models.CharField(
                choices=[
                    ('full_time', 'Полная занятость'),
                    ('part_time', 'Частичная занятость'),
                    ('remote', 'Удалённая работа'),
                    ('hybrid', 'Гибрид'),
                    ('contract', 'Контракт'),
                    ('internship', 'Стажировка'),
                ],
                default='full_time',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='resume_text',
            field=models.TextField(blank=True, verbose_name='Текст резюме'),
        ),
    ]
