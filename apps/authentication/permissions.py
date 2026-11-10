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


class IsAdminOrEngineerForSensorControls(permissions.BasePermission):
    """Инженеры могут менять только значения датчиков и режим их работы."""
    sensor_control_actions = {'set_manual_value', 'toggle_auto'}

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            return True
        return (
            request.user.role == 'ENGINEER'
            and getattr(view, 'action', None) in self.sensor_control_actions
        )