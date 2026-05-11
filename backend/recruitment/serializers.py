from rest_framework import serializers
from .models import Vacancy, Candidate, VacancyQuestion, CandidateAnswer


class VacancyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacancyQuestion
        fields = ['id', 'question_text', 'question_type', 'options', 'is_required', 'order']


class VacancySerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    candidate_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    questions = VacancyQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Vacancy
        fields = '__all__'

    def get_candidate_count(self, obj):
        return obj.candidates.count()


class PublicVacancySerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    questions = VacancyQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Vacancy
        fields = [
            'id', 'title', 'department_name', 'description', 'requirements',
            'responsibilities', 'conditions', 'required_skills', 'experience_years',
            'salary_from', 'salary_to', 'employment_type', 'application_deadline',
            'questions',
        ]


class CandidateAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = CandidateAnswer
        fields = ['id', 'question', 'question_text', 'answer_text']


class CandidateSerializer(serializers.ModelSerializer):
    vacancy_title = serializers.CharField(source='vacancy.title', read_only=True)
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    full_name = serializers.CharField(read_only=True)
    ai_score = serializers.DecimalField(max_digits=5, decimal_places=4, read_only=True)
    ml_hiring_probability = serializers.DecimalField(max_digits=5, decimal_places=4, read_only=True)
    answers = CandidateAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Candidate
        fields = '__all__'
