from rest_framework import permissions


def is_admin(user):
    return bool(user and user.is_authenticated and (user.user_role == 'admin' or user.is_superuser))


def is_team_lead(user):
    return bool(user and user.is_authenticated and user.user_role == 'team_lead')


def is_manager(user):
    return is_admin(user) or is_team_lead(user)


def can_manage_project(user, project):
    if is_admin(user):
        return True
    if not is_team_lead(user):
        return False
    if project.created_by_id == user.id:
        return True
    return project.participants.filter(user=user).exists()


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


class IsManagerRole(permissions.BasePermission):
    message = 'Это действие доступно только администратору или тимлиду.'
    def has_permission(self, request, view):
        return is_manager(request.user)


class ManagerWriteAdminDelete(permissions.BasePermission):

    message = 'Недостаточно прав для этого действия.'
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == 'DELETE':
            return is_admin(request.user)
        return is_manager(request.user)


class IsAuthenticatedReadOnlyOrManager(permissions.BasePermission):
    message = 'Для просмотра нужна авторизация, а для изменения нужен администратор или тимлид.'
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_manager(request.user)
