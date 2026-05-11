import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0003_vacancy_new_fields_candidate_resume_text'),
    ]

    operations = [
        # --- Vacancy public fields (not yet in DB) ---
        # Add public_token without unique first
        migrations.RunSQL(
            "ALTER TABLE recruitment_vacancy ADD COLUMN IF NOT EXISTS public_token uuid DEFAULT NULL;",
            migrations.RunSQL.noop,
        ),
        # Fill NULLs
        migrations.RunSQL(
            """
            DO $$
            DECLARE r RECORD;
            BEGIN
              FOR r IN SELECT id FROM recruitment_vacancy WHERE public_token IS NULL LOOP
                UPDATE recruitment_vacancy SET public_token = gen_random_uuid() WHERE id = r.id;
              END LOOP;
            END $$;
            """,
            migrations.RunSQL.noop,
        ),
        # Set NOT NULL
        migrations.RunSQL(
            "ALTER TABLE recruitment_vacancy ALTER COLUMN public_token SET NOT NULL;",
            migrations.RunSQL.noop,
        ),
        # Add unique constraint (idempotent check)
        migrations.RunSQL(
            """
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'recruitment_vacancy_public_token_key'
                  AND conrelid = 'recruitment_vacancy'::regclass
              ) THEN
                ALTER TABLE recruitment_vacancy ADD CONSTRAINT recruitment_vacancy_public_token_key UNIQUE (public_token);
              END IF;
            END $$;
            """,
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE recruitment_vacancy ADD COLUMN IF NOT EXISTS is_public boolean NOT NULL DEFAULT false;",
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "ALTER TABLE recruitment_vacancy ADD COLUMN IF NOT EXISTS application_deadline date NULL;",
            migrations.RunSQL.noop,
        ),
        # Tell Django state about all vacancy public fields
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='vacancy',
                    name='public_token',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                migrations.AddField(
                    model_name='vacancy',
                    name='is_public',
                    field=models.BooleanField(default=False, verbose_name='Открыта для откликов'),
                ),
                migrations.AddField(
                    model_name='vacancy',
                    name='application_deadline',
                    field=models.DateField(blank=True, null=True, verbose_name='Дедлайн заявок'),
                ),
            ],
            database_operations=[],
        ),
        # --- Candidate source: already in DB, just update state ---
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='candidate',
                    name='source',
                    field=models.CharField(
                        choices=[('hr', 'Добавлен HR'), ('public', 'Публичная форма')],
                        default='hr',
                        max_length=20,
                    ),
                ),
            ],
            database_operations=[],
        ),
        # --- VacancyQuestion: already in DB, just update state ---
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='VacancyQuestion',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('question_text', models.CharField(max_length=500)),
                        ('question_type', models.CharField(
                            choices=[('text', 'Текст'), ('single', 'Один вариант'), ('multiple', 'Несколько вариантов')],
                            default='text',
                            max_length=20,
                        )),
                        ('options', models.JSONField(blank=True, default=list)),
                        ('is_required', models.BooleanField(default=False)),
                        ('order', models.PositiveSmallIntegerField(default=0)),
                        ('vacancy', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='questions',
                            to='recruitment.vacancy',
                        )),
                    ],
                    options={
                        'verbose_name': 'Вопрос вакансии',
                        'verbose_name_plural': 'Вопросы вакансии',
                        'ordering': ['order', 'id'],
                    },
                ),
            ],
            database_operations=[],
        ),
        # --- CandidateAnswer: already in DB, just update state ---
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='CandidateAnswer',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('answer_text', models.TextField(blank=True)),
                        ('candidate', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='answers',
                            to='recruitment.candidate',
                        )),
                        ('question', models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name='answers',
                            to='recruitment.vacancyquestion',
                        )),
                    ],
                    options={
                        'verbose_name': 'Ответ кандидата',
                        'verbose_name_plural': 'Ответы кандидатов',
                    },
                ),
                migrations.AlterUniqueTogether(
                    name='candidateanswer',
                    unique_together={('candidate', 'question')},
                ),
            ],
            database_operations=[],
        ),
    ]
