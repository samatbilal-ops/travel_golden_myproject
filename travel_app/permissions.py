from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    """Оқуға — бәрі, жазуға — тек әкімші (is_staff)."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrStaff(permissions.BasePermission):
    """Объектіні тек иесі немесе әкімші өзгерте/оқи алады."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or getattr(obj, 'user_id', None) == request.user.id


class IsOwnerOrStaffOrReadOnly(IsOwnerOrStaff):
    """Оқуға — бәрі (мысалы, пікірлер), жазуға — иесі немесе әкімші."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_object_permission(request, view, obj)
