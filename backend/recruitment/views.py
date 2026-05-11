import mimetypes
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from accounts.permissions import IsHROrDirector
from .models import Vacancy, Candidate, VacancyQuestion
from .serializers import VacancySerializer, CandidateSerializer, VacancyQuestionSerializer
from .ranking import CandidateRanker, retrain_model

_ranker = CandidateRanker()


class VacancyViewSet(viewsets.ModelViewSet):
    queryset = Vacancy.objects.select_related('department', 'position').all()
    serializer_class = VacancySerializer
    permission_classes = [IsHROrDirector]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering = ['-published_at']

    def get_queryset(self):
        qs = super().get_queryset()
        vac_status = self.request.query_params.get('status')
        dept = self.request.query_params.get('department')
        if vac_status:
            qs = qs.filter(status=vac_status)
        if dept:
            qs = qs.filter(department_id=dept)
        return qs

    def destroy(self, request, *args, **kwargs):
        vacancy = self.get_object()
        active_count = vacancy.candidates.exclude(stage='rejected').count()
        if active_count > 0:
            return Response(
                {'detail': 'Нельзя удалить вакансию с активными кандидатами. Сначала отклоните всех кандидатов.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get', 'post'], url_path='questions')
    def questions(self, request, pk=None):
        vacancy = self.get_object()
        if request.method == 'GET':
            qs = vacancy.questions.all()
            return Response(VacancyQuestionSerializer(qs, many=True).data)
        serializer = VacancyQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(vacancy=vacancy)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'questions/(?P<qid>\d+)')
    def delete_question(self, request, pk=None, qid=None):
        vacancy = self.get_object()
        try:
            q = vacancy.questions.get(id=qid)
        except VacancyQuestion.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        q.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'], url_path='publish')
    def publish(self, request, pk=None):
        vacancy = self.get_object()
        is_public = request.data.get('is_public')
        application_deadline = request.data.get('application_deadline')
        if is_public is not None:
            vacancy.is_public = bool(is_public)
        if application_deadline is not None:
            vacancy.application_deadline = application_deadline or None
        vacancy.save(update_fields=['is_public', 'application_deadline'])
        return Response(VacancySerializer(vacancy).data)

    @action(detail=True, methods=['post'], url_path='analyze_all')
    def analyze_all(self, request, pk=None):
        """POST /api/recruitment/vacancies/{id}/analyze_all/ — AI-анализ всех кандидатов вакансии."""
        vacancy = self.get_object()
        all_candidates = list(vacancy.candidates.all())
        updated = []
        for candidate in all_candidates:
            result = _ranker.analyze(candidate, vacancy, all_candidates)
            candidate.ai_score = result['ai_score']
            candidate.ml_hiring_probability = result['ml_hiring_probability']
            candidate.extracted_skills = result['extracted_skills']
            candidate.ai_comment = result['ai_comment']
            candidate.save(update_fields=['ai_score', 'ml_hiring_probability', 'extracted_skills', 'ai_comment'])
            updated.append(CandidateSerializer(candidate).data)
        return Response({'analyzed': len(updated), 'candidates': updated})


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.select_related('vacancy').all()
    serializer_class = CandidateSerializer
    permission_classes = [IsHROrDirector]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email']
    ordering = ['-applied_at']

    def get_queryset(self):
        qs = super().get_queryset()
        vacancy = self.request.query_params.get('vacancy')
        stage = self.request.query_params.get('stage')
        if vacancy:
            qs = qs.filter(vacancy_id=vacancy)
        if stage:
            qs = qs.filter(stage=stage)
        return qs

    @action(detail=True, methods=['post'])
    def advance_stage(self, request, pk=None):
        stages = ['new', 'screening', 'interview', 'offer', 'hired']
        candidate = self.get_object()
        model_retrained = False
        if candidate.stage in stages:
            idx = stages.index(candidate.stage)
            if idx < len(stages) - 1:
                candidate.stage = stages[idx + 1]
                if candidate.stage == 'hired':
                    candidate.hiring_result = True
                    candidate.save()
                    model_retrained = retrain_model()
                else:
                    candidate.save()
        return Response({**CandidateSerializer(candidate).data, 'model_retrained': model_retrained})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """POST /api/recruitment/candidates/{id}/reject/ — перевести в отклонён."""
        candidate = self.get_object()
        candidate.stage = 'rejected'
        candidate.hiring_result = False
        candidate.save()
        model_retrained = retrain_model()
        return Response({**CandidateSerializer(candidate).data, 'model_retrained': model_retrained})

    @action(detail=True, methods=['post'], url_path='analyze')
    def analyze(self, request, pk=None):
        """POST /api/recruitment/candidates/{id}/analyze/ — AI-анализ одного кандидата."""
        candidate = self.get_object()
        vacancy = candidate.vacancy
        all_candidates = list(vacancy.candidates.all())
        result = _ranker.analyze(candidate, vacancy, all_candidates)
        candidate.ai_score = result['ai_score']
        candidate.ml_hiring_probability = result['ml_hiring_probability']
        candidate.extracted_skills = result['extracted_skills']
        candidate.ai_comment = result['ai_comment']
        candidate.save(update_fields=['ai_score', 'ml_hiring_probability', 'extracted_skills', 'ai_comment'])
        return Response(CandidateSerializer(candidate).data)


class _QueryOrHeaderJWT(JWTAuthentication):
    """Принимает JWT из Authorization-заголовка ИЛИ из ?token= query-параметра.

    Нужно для открытия файла в новой вкладке браузера: браузер не отправляет
    заголовок Authorization при прямой навигации, поэтому токен передаётся
    в URL.  Этот аутентификатор запускается в DRF initial(), то есть ДО
    проверки прав — в отличие от ручного вызова внутри метода get().
    """

    def authenticate(self, request):
        # 1. Стандартная проверка через Authorization: Bearer ...
        result = super().authenticate(request)
        if result is not None:
            return result

        # 2. Fallback — ?token=<jwt>
        token_str = request.query_params.get('token', '').strip()
        if not token_str:
            return None
        try:
            validated = self.get_validated_token(token_str.encode())
            return self.get_user(validated), validated
        except (InvalidToken, TokenError):
            return None


class CandidateResumeView(APIView):
    """GET /api/recruitment/candidates/<pk>/resume/

    Отдаёт файл резюме кандидата.
    Аутентификация: Bearer-заголовок ИЛИ ?token=<access_token> (прямая вкладка).
    """

    authentication_classes = [_QueryOrHeaderJWT]
    permission_classes = [IsHROrDirector]

    def get(self, request, pk):
        candidate = get_object_or_404(Candidate, pk=pk)

        if not candidate.resume or not candidate.resume.name:
            from rest_framework.exceptions import NotFound
            raise NotFound('Файл резюме не прикреплён')

        try:
            f = candidate.resume.open('rb')
        except (FileNotFoundError, OSError):
            from rest_framework.exceptions import NotFound
            raise NotFound('Файл резюме не найден на сервере')

        mime, _ = mimetypes.guess_type(candidate.resume.name)
        mime = mime or 'application/octet-stream'
        filename = candidate.resume.name.split('/')[-1]

        response = FileResponse(f, content_type=mime)
        disposition = 'inline' if mime == 'application/pdf' else 'attachment'
        response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
        return response
