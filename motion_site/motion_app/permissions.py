from rest_framework import permissions


def is_admin(user):
    return bool(user and user.is_authenticated and user.user_role == 'admin')


class IsAdminRole(permissions.BasePermission):
    message = 'Это действие доступно только администратору.'
    def has_permission(self, request, view):
        return is_admin(request.user)


class ReadOnlyOrAdmin(permissions.BasePermission):
    message = 'Изменять данные может только администратор.'
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_admin(request.user)


class IsAuthenticatedReadOnlyOrAdmin(permissions.BasePermission):
    message = 'Для просмотра нужна авторизация, а для изменения нужен администратор.'
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_admin(request.user)


class ReviewPermission(permissions.BasePermission):
    message = 'Изменять или удалять чужой отзыв может только администратор.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_admin(request.user) or obj.user_id == request.user.id