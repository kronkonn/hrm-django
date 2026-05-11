import uuid
from django.db import models
from employees.models import Department, Position


class Vacancy(models.Model):
    STATUS_CHOICES = [
        ('open', 'Открыта'),
        ('closed', 'Закрыта'),
        ('on_hold', 'Приостановлена'),
    ]
    EMPLOYMENT_CHOICES = [
        ('full_time', 'Полная занятость'),
        ('part_time', 'Частичная занятость'),
        ('remote', 'Удалённая работа'),
        ('hybrid', 'Гибрид'),
        ('contract', 'Контракт'),
        ('internship', 'Стажировка'),
    ]

    title = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='vacancies')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='vacancies')
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True, verbose_name='Обязанности')
    conditions = models.TextField(blank=True, verbose_name='Условия работы')
    required_skills = models.JSONField(default=list, blank=True, verbose_name='Требуемые навыки')
    experience_years = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Опыт (лет)')
    salary_from = models.IntegerField(null=True, blank=True, verbose_name='Зарплата от')
    salary_to = models.IntegerField(null=True, blank=True, verbose_name='Зарплата до')
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES, default='full_time')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    published_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Public application
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_public = models.BooleanField(default=False, verbose_name='Открыта для откликов')
    application_deadline = models.DateField(null=True, blank=True, verbose_name='Дедлайн заявок')

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'
        ordering = ['-published_at']

    def __str__(self):
        return f'{self.title} ({self.department})'


class Candidate(models.Model):
    STAGE_CHOICES = [
        ('new', 'Новый'),
        ('screening', 'Скрининг'),
        ('interview', 'Интервью'),
        ('offer', 'Оффер'),
        ('hired', 'Принят'),
        ('rejected', 'Отклонён'),
    ]

    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='candidates')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    resume_text = models.TextField(blank=True, verbose_name='Текст резюме')
    cover_letter = models.TextField(blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='new')
    rating = models.PositiveSmallIntegerField(default=0, help_text='0–5')
    notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # AI ranking fields
    ai_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True,
                                   verbose_name='AI-оценка')
    ml_hiring_probability = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True,
                                                verbose_name='Вероятность найма (ML)')
    extracted_skills = models.JSONField(default=list, blank=True, verbose_name='Извлечённые навыки')
    ai_comment = models.TextField(blank=True, verbose_name='AI-комментарий')

    hiring_result = models.BooleanField(null=True, blank=True, verbose_name='Результат найма')

    SOURCE_CHOICES = [
        ('hr', 'Добавлен HR'),
        ('public', 'Публичная форма'),
    ]

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='hr')

    class Meta:
        verbose_name = 'Кандидат'
        verbose_name_plural = 'Кандидаты'
        ordering = ['-applied_at']

    def __str__(self):
        return f'{self.last_name} {self.first_name} → {self.vacancy.title}'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name}'


class VacancyQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('text', 'Текст'),
        ('single', 'Один вариант'),
        ('multiple', 'Несколько вариантов'),
    ]

    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='text')
    options = models.JSONField(default=list, blank=True)
    is_required = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = 'Вопрос вакансии'
        verbose_name_plural = 'Вопросы вакансии'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.vacancy.title}: {self.question_text[:50]}'


class CandidateAnswer(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(VacancyQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ответ кандидата'
        verbose_name_plural = 'Ответы кандидатов'
        unique_together = [('candidate', 'question')]

    def __str__(self):
        return f'{self.candidate.full_name} → {self.question.question_text[:40]}'
