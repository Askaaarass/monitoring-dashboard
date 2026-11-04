from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """Доступ разрешен только пользователям с ролью ADMIN или Superuser"""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == 'ADMIN' or request.user.is_superuser)
        )

class IsAdminOrReadOnly(permissions.BasePermission):
    """Чтение доступно всем, изменение — только администраторам."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == 'ADMIN' or request.user.is_superuser)
        )