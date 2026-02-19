from rest_framework.permissions import BasePermission, SAFE_METHODS


def _role(user) -> str:
    """Foydalanuvchi rolini qaytaradi. superuser/staff -> MANAGER."""
    if not user or not user.is_authenticated:
        return ""
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return "MANAGER"
    return getattr(user, "role", "")


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) == "MANAGER"


class IsWaiter(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) == "WAITER"


class IsChef(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) == "CHEF"


class ManagerOrReadOnly(BasePermission):
    """GET, HEAD, OPTIONS — barcha autentifikatsiyalangan; o'zgartirish — faqat MANAGER."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return _role(request.user) == "MANAGER"
