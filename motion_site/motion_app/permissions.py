from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.user_role == 'admin'
        )


class ReadOnlyOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.user_role == 'admin'
        )


class IsProjectMemberOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if user.user_role == 'admin':
            return True
        return obj.project.participants.filter(user=user).exists()