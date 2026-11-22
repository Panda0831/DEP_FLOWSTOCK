from rest_framework.permissions import BasePermission


def has_role(user, *roles):
    if not user or not user.is_authenticated:
        return False
    if "ADMIN" in roles and getattr(user, "is_superuser", False):
        return True
    return getattr(user, "role", None) in roles


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return has_role(request.user, "ADMIN")


class IsAuthenticatedRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
