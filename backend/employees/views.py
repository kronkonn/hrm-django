from django.db.models import Count
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.permissions import IsHROrDirector
from .models import Employee, Department, Position
from .serializers import EmployeeListSerializer, EmployeeDetailSerializer, DepartmentSerializer, PositionSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsHROrDirector]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.select_related('department').all()
    serializer_class = PositionSerializer
    permission_classes = [IsHROrDirector]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title']
    ordering_fields = ['title', 'salary_min']


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('department', 'position', 'manager').prefetch_related('leave_requests').all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['last_name', 'hire_date', 'salary', 'department__name']
    ordering = ['last_name']

    def get_permissions(self):
        # EMPLOYEE может читать только свою запись (через /me/employee/ или detail)
        # Список и изменения — только HR+
        if self.action in ('list', 'create', 'update', 'partial_update', 'destroy', 'stats'):
            return [IsHROrDirector()]
        # retrieve (GET /employees/{id}/) — проверяем отдельно в get_object
        return [IsHROrDirector()]

    def get_queryset(self):
        qs = super().get_queryset()
        dept = self.request.query_params.get('department')
        status = self.request.query_params.get('status')
        if dept:
            qs = qs.filter(department_id=dept)
        if status:
            qs = qs.filter(status=status)
        return qs

    @action(detail=False, methods=['get'])
    def stats(self, request):
        total = Employee.objects.filter(status='active').count()
        by_dept = list(
            Employee.objects.filter(status='active')
            .values('department__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return Response({'total_active': total, 'by_department': by_dept})

    @action(detail=False, methods=['get'], url_path='me', permission_classes=[])
    def me(self, request):
        """Собственная карточка сотрудника (доступна любому аутентифицированному)."""
        if not request.user.is_authenticated:
            return Response(status=401)
        profile = getattr(request.user, 'profile', None)
        if not profile or not profile.employee:
            return Response({'detail': 'Профиль сотрудника не найден.'}, status=404)
        serializer = EmployeeDetailSerializer(profile.employee)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer
