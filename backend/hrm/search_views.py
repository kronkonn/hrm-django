from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.permissions import IsHRDirectorOrAdmin


class GlobalSearchView(APIView):
    """GET /api/search/?q=текст — поиск по сотрудникам, вакансиям, кандидатам."""
    permission_classes = [IsHRDirectorOrAdmin]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'employees': [], 'vacancies': [], 'candidates': []})

        from employees.models import Employee
        from recruitment.models import Vacancy, Candidate

        employees = (
            Employee.objects
            .select_related('position', 'department')
            .filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(middle_name__icontains=q) |
                Q(email__icontains=q) |
                Q(position__title__icontains=q) |
                Q(department__name__icontains=q)
            )
            .filter(status='active')[:6]
        )

        vacancies = (
            Vacancy.objects
            .select_related('department')
            .filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(department__name__icontains=q)
            )[:6]
        )

        candidates = (
            Candidate.objects
            .select_related('vacancy')
            .filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q)
            )[:6]
        )

        return Response({
            'employees': [
                {
                    'id': e.id,
                    'full_name': f'{e.last_name} {e.first_name} {e.middle_name or ""}'.strip(),
                    'position': e.position.title if e.position else '',
                    'department': e.department.name if e.department else '',
                }
                for e in employees
            ],
            'vacancies': [
                {
                    'id': v.id,
                    'title': v.title,
                    'department': v.department.name if v.department else '',
                    'status': v.status,
                    'status_display': v.get_status_display(),
                }
                for v in vacancies
            ],
            'candidates': [
                {
                    'id': c.id,
                    'full_name': c.full_name,
                    'email': c.email,
                    'vacancy_title': c.vacancy.title,
                    'stage': c.stage,
                    'stage_display': c.get_stage_display(),
                }
                for c in candidates
            ],
        })
