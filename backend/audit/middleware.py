"""
AuditMiddleware — автоматическое логирование действий пользователей.
Логирует LOGIN, LOGOUT, CREATE (POST→201), UPDATE (PUT/PATCH→200), DELETE (DELETE→204/200).
"""
import json
import re

_SKIP_PATHS = frozenset([
    '/api/auth/token/refresh/',
    '/api/search/',
    '/admin/',
])

_SENSITIVE_KEYS = frozenset([
    'password', 'token', 'access', 'refresh',
    'new_password', 'old_password', 'current_password',
])

# URL segments → display model name
_MODEL_NAME: dict[tuple, str] = {
    ('employees',):                'Employee',
    ('leaves',):                   'LeaveRequest',
    ('timesheets',):               'Timesheet',
    ('recruitment', 'vacancies'):  'Vacancy',
    ('recruitment', 'candidates'): 'Candidate',
    ('analytics', 'attrition'):    'AttritionPrediction',
    ('analytics', 'anomalies'):    'Anomaly',
    ('analytics', 'clusters'):     'EmployeeCluster',
    ('analytics', 'run_all'):      'Analytics',
    ('training', 'courses'):       'Course',
    ('training', 'assignments'):   'CourseAssignment',
    ('auth', 'users'):             'User',
}


def _get_ip(request) -> str | None:
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


def _parse_path(path: str) -> tuple[str, str | None]:
    """Returns (model_name, object_id) from /api/... path."""
    if not path.startswith('/api/'):
        return '', None
    parts = [p for p in path[5:].split('/') if p]
    if not parts:
        return '', None

    object_id = None
    if parts and parts[-1].isdigit():
        object_id = parts[-1]
        parts = parts[:-1]

    model_name = _MODEL_NAME.get(tuple(parts))
    if model_name is None:
        # Fallback: capitalise first segment
        model_name = parts[0].capitalize() if parts else ''
    return model_name, object_id


def _read_body(request) -> dict | None:
    ct = request.content_type or ''
    if 'json' not in ct:
        return None
    try:
        data = json.loads(request.body.decode('utf-8'))
        if not isinstance(data, dict):
            return None
        return {k: ('***' if k in _SENSITIVE_KEYS else v) for k, v in data.items()}
    except Exception:
        return None


def _read_response(response) -> dict | None:
    try:
        ct = response.get('Content-Type', '')
        if 'json' not in ct:
            return None
        data = json.loads(response.content.decode('utf-8'))
        if not isinstance(data, dict):
            return None
        return {k: ('***' if k in _SENSITIVE_KEYS else v) for k, v in data.items()}
    except Exception:
        return None


def _save(user, action, model_name, object_id, object_repr, changes, ip, details):
    """Saves AuditLog; never raises."""
    try:
        from audit.models import AuditLog
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id or '',
            object_repr=object_repr or '',
            changes=changes,
            ip_address=ip,
            details=details,
        )
    except Exception:
        pass


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path   = request.path
        method = request.method

        # Pre-read body (Django caches request.body so view still gets it)
        body = None
        if method in ('POST', 'PUT', 'PATCH'):
            body = _read_body(request)

        response = self.get_response(request)

        # Only log successful API responses
        if response.status_code >= 400:
            return response

        # Skip non-API, refresh, and admin paths
        if not path.startswith('/api/') or any(path.startswith(s) for s in _SKIP_PATHS):
            return response

        ip   = _get_ip(request)
        user = request.user if request.user.is_authenticated else None

        # ── LOGIN ─────────────────────────────────────────────────────────────
        if path == '/api/auth/token/' and method == 'POST' and response.status_code == 200:
            # JWT auth: request.user is AnonymousUser here, find user by username
            if not user and body and 'username' in body:
                from django.contrib.auth.models import User as DjUser
                try:
                    user = DjUser.objects.get(username=body['username'])
                except DjUser.DoesNotExist:
                    pass
            _save(user, 'LOGIN', 'User', str(user.id) if user else '', str(user) if user else '',
                  None, ip, f'Успешный вход: {user}')
            return response

        # ── LOGOUT ────────────────────────────────────────────────────────────
        if path == '/api/auth/logout/' and method == 'POST' and response.status_code == 200:
            _save(user, 'LOGOUT', 'User', str(user.id) if user else '', str(user) if user else '',
                  None, ip, f'Выход из системы: {user}')
            return response

        # ── CRUD ──────────────────────────────────────────────────────────────
        model_name, object_id = _parse_path(path)
        if not model_name:
            return response

        action       = None
        changes      = None
        object_repr  = ''
        details      = ''

        if method == 'POST' and response.status_code in (200, 201):
            action = 'CREATE'
            resp_data = _read_response(response)
            if resp_data:
                object_id   = str(resp_data.get('id', object_id or ''))
                object_repr = resp_data.get('__str__') or f'{model_name} #{object_id}'
                changes     = {k: v for k, v in resp_data.items()
                               if k not in ('id', '__str__') and k not in _SENSITIVE_KEYS}
            details = f'Создан {model_name} id={object_id}'

        elif method in ('PUT', 'PATCH') and response.status_code in (200, 201):
            action = 'UPDATE'
            if body:
                changes = {'updated_fields': body}
            details = f'Изменён {model_name} id={object_id}'

        elif method == 'DELETE' and response.status_code in (200, 204):
            action = 'DELETE'
            details = f'Удалён {model_name} id={object_id}'

        if action:
            _save(user, action, model_name, object_id, object_repr, changes, ip, details)

        return response
