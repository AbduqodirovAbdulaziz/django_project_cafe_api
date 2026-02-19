from rest_framework.permissions import BasePermission, SAFE_METHODS


def _role(user) -> str:
    """Foydalanuvchi rolini qaytaradi. superuser/staff -> MANAGER."""
    if not user or not user.is_authenticated:
        return ""
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return "MANAGER"
    return getattr(user, "role", "")


class IsManager(BasePermission):
    message = "Faqat MANAGER ruxsati bor."

    def has_permission(self, request, view):
        return _role(request.user) == "MANAGER"


class IsWaiter(BasePermission):
    message = "Faqat WAITER ruxsati bor."

    def has_permission(self, request, view):
        return _role(request.user) == "WAITER"


class IsChef(BasePermission):
    message = "Faqat CHEF ruxsati bor."

    def has_permission(self, request, view):
        return _role(request.user) == "CHEF"


class IsManagerOrWaiter(BasePermission):
    message = "Faqat MANAGER yoki WAITER ruxsati bor."

    def has_permission(self, request, view):
        return _role(request.user) in ("MANAGER", "WAITER")


class IsManagerOrChef(BasePermission):
    message = "Faqat MANAGER yoki CHEF ruxsati bor."

    def has_permission(self, request, view):
        return _role(request.user) in ("MANAGER", "CHEF")


class ManagerOrReadOnly(BasePermission):
    """GET, HEAD, OPTIONS — barcha autentifikatsiyalangan; o'zgartirish — faqat MANAGER."""
    message = "O'zgartirish uchun faqat MANAGER ruxsati bor."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return _role(request.user) == "MANAGER"
