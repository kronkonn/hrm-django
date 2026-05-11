from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from accounts.permissions import IsAdmin
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/audit/logs/ — журнал аудита. Только для ADMIN."""
    queryset           = AuditLog.objects.select_related('user').all()
    serializer_class   = AuditLogSerializer
    permission_classes = [IsAdmin]
    pagination_class   = AuditPagination
    filter_backends    = [filters.OrderingFilter]
    ordering           = ['-timestamp']

    def get_queryset(self):
        qs = super().get_queryset()
        p  = self.request.query_params

        user_id   = p.get('user')
        action    = p.get('action')
        model     = p.get('model')
        date_from = p.get('date_from')
        date_to   = p.get('date_to')
        search    = p.get('search')

        if user_id:
            qs = qs.filter(user_id=user_id)
        if action:
            qs = qs.filter(action=action)
        if model:
            qs = qs.filter(model_name__icontains=model)
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(user__username__icontains=search) |
                Q(model_name__icontains=search) |
                Q(object_repr__icontains=search) |
                Q(details__icontains=search)
            )
        return qs
