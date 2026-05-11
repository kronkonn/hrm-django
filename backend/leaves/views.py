from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from accounts.permissions import IsHROrDirector
from .models import LeaveRequest, SickLeaveDetails
from .serializers import LeaveRequestSerializer, SickLeaveDetailsSerializer


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related('employee', 'approved_by').all()
    serializer_class = LeaveRequestSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']

    def get_permissions(self):
        # Любой аутентифицированный может создать заявку и читать свои
        if self.action in ('list', 'retrieve', 'create'):
            return [IsAuthenticated()]
        # Обновление/удаление/approve/reject — только HR+
        return [IsHROrDirector()]

    def get_queryset(self):
        qs = super().get_queryset()
        profile = getattr(self.request.user, 'profile', None)
        role = profile.role if profile else None

        # EMPLOYEE видит только свои заявки
        if role == 'EMPLOYEE':
            emp = profile.employee if profile else None
            qs = qs.filter(employee=emp) if emp else qs.none()
        else:
            # HR/DIRECTOR/ADMIN — фильтры из query params
            emp_id = self.request.query_params.get('employee')
            leave_status = self.request.query_params.get('status')
            leave_type = self.request.query_params.get('leave_type')
            if emp_id:
                qs = qs.filter(employee_id=emp_id)
            if leave_status:
                qs = qs.filter(status=leave_status)
            if leave_type:
                qs = qs.filter(leave_type=leave_type)

        return qs

    def perform_create(self, serializer):
        profile = getattr(self.request.user, 'profile', None)
        role = profile.role if profile else None
        if role == 'EMPLOYEE' and profile and profile.employee:
            leave = serializer.save(employee=profile.employee)
        else:
            leave = serializer.save()
        if leave.leave_type == 'sick':
            SickLeaveDetails.objects.get_or_create(leave_request=leave)

    @action(detail=True, methods=['patch'], url_path='sick_details')
    def sick_details(self, request, pk=None):
        leave = self.get_object()
        if leave.leave_type != 'sick':
            return Response({'detail': 'Не является больничным.'}, status=status.HTTP_400_BAD_REQUEST)
        details, _ = SickLeaveDetails.objects.get_or_create(leave_request=leave)
        serializer = SickLeaveDetailsSerializer(details, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'approved'
        leave.approved_at = timezone.now()
        leave.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave = self.get_object()
        leave.status = 'rejected'
        leave.save()
        return Response({'status': 'rejected'})
