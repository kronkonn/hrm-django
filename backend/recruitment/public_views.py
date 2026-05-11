import logging
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Vacancy, Candidate, VacancyQuestion, CandidateAnswer
from .serializers import PublicVacancySerializer
from .ranking import CandidateRanker

logger = logging.getLogger(__name__)


def _extract_text(file_obj) -> str:
    if not file_obj:
        return ''
    name = file_obj.name.lower()
    try:
        if name.endswith('.pdf'):
            import pdfplumber
            with pdfplumber.open(file_obj) as pdf:
                return '\n'.join(p.extract_text() or '' for p in pdf.pages)
        if name.endswith('.docx'):
            import docx
            doc = docx.Document(file_obj)
            return '\n'.join(p.text for p in doc.paragraphs)
    except Exception as e:
        logger.warning('Resume extraction failed: %s', e)
    return ''


@api_view(['GET'])
@permission_classes([AllowAny])
def public_vacancy_detail(request, token):
    try:
        vacancy = Vacancy.objects.select_related('department').prefetch_related('questions').get(
            public_token=token, is_public=True,
        )
    except Vacancy.DoesNotExist:
        return Response({'detail': 'Вакансия не найдена или закрыта.'}, status=status.HTTP_404_NOT_FOUND)

    if vacancy.application_deadline and vacancy.application_deadline < timezone.now().date():
        return Response({'detail': 'Срок подачи заявок истёк.'}, status=status.HTTP_410_GONE)

    return Response(PublicVacancySerializer(vacancy).data)


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def public_vacancy_apply(request, token):
    try:
        vacancy = Vacancy.objects.prefetch_related('questions').get(
            public_token=token, is_public=True,
        )
    except Vacancy.DoesNotExist:
        return Response({'detail': 'Вакансия не найдена или закрыта.'}, status=status.HTTP_404_NOT_FOUND)

    if vacancy.application_deadline and vacancy.application_deadline < timezone.now().date():
        return Response({'detail': 'Срок подачи заявок истёк.'}, status=status.HTTP_410_GONE)

    data = request.data
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    email = (data.get('email') or '').strip()

    if not first_name or not last_name or not email:
        return Response({'detail': 'Обязательные поля: first_name, last_name, email.'}, status=status.HTTP_400_BAD_REQUEST)

    resume_file = request.FILES.get('resume')
    resume_text = (data.get('resume_text') or '').strip()
    if resume_file and not resume_text:
        resume_text = _extract_text(resume_file)

    candidate = Candidate.objects.create(
        vacancy=vacancy,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=(data.get('phone') or '').strip(),
        cover_letter=(data.get('cover_letter') or '').strip(),
        resume_text=resume_text,
        resume=resume_file,
        source='public',
        stage='new',
    )

    # Save questionnaire answers
    questions = {q.id: q for q in vacancy.questions.all()}
    for qid, question in questions.items():
        key = f'answer_{qid}'
        answer_val = data.get(key, '')
        if isinstance(answer_val, list):
            answer_val = ', '.join(answer_val)
        CandidateAnswer.objects.create(
            candidate=candidate,
            question=question,
            answer_text=str(answer_val).strip(),
        )

    # AI ranking
    try:
        all_cands = list(Candidate.objects.filter(vacancy=vacancy))
        result = CandidateRanker().analyze(candidate, vacancy, all_candidates=all_cands)
        candidate.ai_score = result['ai_score']
        candidate.ml_hiring_probability = result['ml_hiring_probability']
        candidate.extracted_skills = result['extracted_skills']
        candidate.ai_comment = result['ai_comment']
        candidate.save(update_fields=['ai_score', 'ml_hiring_probability', 'extracted_skills', 'ai_comment'])
    except Exception as e:
        logger.warning('AI ranking failed for public candidate %s: %s', candidate.id, e)

    return Response({'detail': 'Заявка принята. Спасибо!', 'candidate_id': candidate.id}, status=status.HTTP_201_CREATED)
