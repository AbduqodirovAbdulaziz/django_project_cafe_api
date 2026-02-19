from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from accounts.permissions import _role
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import User

ROLE_COLORS = {
    "MANAGER": "#16a085",
    "WAITER":  "#2980b9",
    "CHEF":    "#e67e22",
}


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form     = CustomUserChangeForm
    model    = User

    list_display  = ("username", "full_name", "role_badge", "is_active_badge", "is_staff", "date_joined")
    list_filter   = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering      = ("username",)

    fieldsets = (
        (None,                  {"fields": ("username", "password")}),
        ("Shaxsiy ma'lumotlar", {"fields": ("first_name", "last_name", "email")}),
        ("Rol",                 {"fields": ("role",)}),
        ("Ruxsatlar",           {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Muhim sanalar",       {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "first_name", "last_name", "role", "password1", "password2"),
        }),
    )

    def has_add_permission(self, request):
        return _role(request.user) == "MANAGER"

    def has_change_permission(self, request, obj=None):
        role = _role(request.user)
        if role == "MANAGER":
            return True
        # Boshqa rollar faqat o'zini ko'radi
        if obj is not None:
            return obj.pk == request.user.pk
        return False

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if _role(request.user) == "MANAGER":
            return qs
        # WAITER va CHEF faqat o'zini ko'radi
        return qs.filter(pk=request.user.pk)

    def get_readonly_fields(self, request, obj=None):
        role = _role(request.user)
        if role == "MANAGER":
            return ("last_login", "date_joined")
        # Boshqalar o'z profilida ko'p narsani o'zgartira olmaydi
        return ("username", "role", "is_staff", "is_superuser",
                "groups", "user_permissions", "last_login", "date_joined")

    def get_fieldsets(self, request, obj=None):
        role = _role(request.user)
        if role != "MANAGER" and obj is not None:
            # Oddiy foydalanuvchi faqat o'z shaxsiy ma'lumotlarini ko'radi
            return (
                ("Shaxsiy ma'lumotlar", {"fields": ("first_name", "last_name", "email")}),
                ("Parol", {"fields": ("password",)}),
            )
        return self.fieldsets

    # ── Display metodlar ──
    @admin.display(description="Ism Familiya")
    def full_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full or "—"

    @admin.display(description="Rol")
    def role_badge(self, obj):
        color = ROLE_COLORS.get(obj.role, "#999")
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:.82rem;font-weight:600;">{}</span>',
            color, obj.get_role_display()
        )

    @admin.display(description="Faol")
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#27ae60;">✓</span>')
        return format_html('<span style="color:#e74c3c;">✗</span>')
