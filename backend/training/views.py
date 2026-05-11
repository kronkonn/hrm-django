import uuid
from datetime import date, timedelta

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsHROrDirector
from .models import Course, CourseAssignment, Certificate
from .serializers import (
    CourseSerializer,
    CourseAssignmentSerializer,
    CourseAssignmentDetailSerializer,
    CertificateSerializer,
)


def _get_role(user):
    profile = getattr(user, 'profile', None)
    return profile.role if profile else None


def _sync_training_count(employee):
    one_year_ago = timezone.now() - timedelta(days=365)
    count = CourseAssignment.objects.filter(
        employee=employee,
        status='completed',
        completed_at__gte=one_year_ago,
    ).count()
    employee.training_times_last_year = count
    employee.save(update_fields=['training_times_last_year'])


def _finish_assignment(obj):
    """Mark assignment completed, create certificate, sync training count."""
    obj.status       = 'completed'
    obj.completed_at = timezone.now()
    obj.save()
    Certificate.objects.get_or_create(
        employee=obj.employee,
        course=obj.course,
        defaults={
            'issued_at':          date.today(),
            'certificate_number': f'CERT-{uuid.uuid4().hex[:8].upper()}',
        },
    )
    _sync_training_count(obj.employee)


class CourseViewSet(viewsets.ModelViewSet):
    queryset         = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsHROrDirector()]

    def get_queryset(self):
        qs     = super().get_queryset()
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        course       = self.get_object()
        employee_ids = request.data.get('employee_ids', [])
        if not isinstance(employee_ids, list):
            return Response({'error': 'employee_ids must be a list'}, status=400)
        assigned = skipped = 0
        for emp_id in employee_ids:
            _, created = CourseAssignment.objects.get_or_create(
                course=course, employee_id=emp_id,
                defaults={'status': 'assigned', 'progress': 0, 'completed_lessons': []},
            )
            if created:
                assigned += 1
            else:
                skipped += 1
        return Response({'assigned': assigned, 'skipped': skipped})


class CourseAssignmentViewSet(viewsets.ModelViewSet):
    queryset = CourseAssignment.objects.select_related(
        'course', 'employee', 'employee__department',
    ).all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseAssignmentDetailSerializer
        return CourseAssignmentSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        qs   = super().get_queryset()
        role = _get_role(self.request.user)

        if role == 'EMPLOYEE':
            profile = getattr(self.request.user, 'profile', None)
            emp     = profile.employee if profile else None
            return qs.filter(employee=emp) if emp else qs.none()

        status      = self.request.query_params.get('status')
        dept        = self.request.query_params.get('department')
        employee_id = self.request.query_params.get('employee')
        if status:
            qs = qs.filter(status=status)
        if dept:
            qs = qs.filter(employee__department_id=dept)
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs

    @action(detail=True, methods=['patch'], url_path='complete-lesson')
    def complete_lesson(self, request, pk=None):
        obj       = self.get_object()
        lesson_id = request.data.get('lesson_id')
        if lesson_id is None:
            return Response({'error': 'lesson_id is required'}, status=400)

        lesson_id = int(lesson_id)
        lessons   = obj.course.lessons or []
        total     = len(lessons)
        if total == 0:
            return Response({'error': 'Course has no lessons'}, status=400)

        completed = list(obj.completed_lessons or [])
        if lesson_id not in completed:
            completed.append(lesson_id)
        obj.completed_lessons = completed

        progress     = min(round(len(completed) / total * 100), 100)
        obj.progress = progress
        was_complete = obj.status == 'completed'

        if progress >= 100 and not was_complete:
            _finish_assignment(obj)
        elif progress > 0 and obj.status == 'assigned':
            obj.status = 'in_progress'
            obj.save()
        else:
            obj.save()

        return Response(CourseAssignmentDetailSerializer(obj).data)

    @action(detail=True, methods=['patch'], url_path='progress')
    def update_progress(self, request, pk=None):
        """Legacy endpoint — manual override (HR/admin use)."""
        obj          = self.get_object()
        progress_val = request.data.get('progress')
        if progress_val is None:
            return Response({'error': 'progress is required'}, status=400)

        progress     = max(0, min(100, int(progress_val)))
        was_complete = obj.status == 'completed'
        obj.progress = progress

        if progress >= 100 and not was_complete:
            _finish_assignment(obj)
        elif progress > 0 and obj.status == 'assigned':
            obj.status = 'in_progress'
            obj.save()
        else:
            obj.save()

        return Response(CourseAssignmentSerializer(obj).data)


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Certificate.objects.select_related(
        'employee', 'course', 'employee__department',
    ).all()
    serializer_class = CertificateSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        qs   = super().get_queryset()
        role = _get_role(self.request.user)
        if role == 'EMPLOYEE':
            profile = getattr(self.request.user, 'profile', None)
            emp     = profile.employee if profile else None
            qs      = qs.filter(employee=emp) if emp else qs.none()
        course_id = self.request.query_params.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs
