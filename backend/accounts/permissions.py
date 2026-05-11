from rest_framework.permissions import BasePermission


def _get_role(user):
    """Возвращает роль пользователя или None."""
    profile = getattr(user, 'profile', None)
    return profile.role if profile else None


class IsDirector(BasePermission):
    """Роли DIRECTOR или ADMIN."""
    message = 'Доступ разрешён директору и администратору.'

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            _get_role(request.user) in ('DIRECTOR', 'ADMIN')
        )


class IsHROrDirector(BasePermission):
    """Роли HR_MANAGER, DIRECTOR или ADMIN."""
    message = 'Доступ разрешён HR-менеджеру, директору и администратору.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            _get_role(request.user) in ('DIRECTOR', 'HR_MANAGER', 'ADMIN')
        )


class IsAdmin(BasePermission):
    """Только роль ADMIN."""
    message = 'Доступ разрешён только администратору.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and _get_role(request.user) == 'ADMIN')


class IsHRDirectorOrAdmin(BasePermission):
    """Роли HR_MANAGER, DIRECTOR или ADMIN."""
    message = 'Недостаточно прав.'

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            _get_role(request.user) in ('DIRECTOR', 'HR_MANAGER', 'ADMIN')
        )


class IsAnyRole(BasePermission):
    """Любой аутентифицированный пользователь с профилем."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            _get_role(request.user) is not None
        )
