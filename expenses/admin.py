from django.contrib import admin
from django.utils.html import format_html

from accounts.permissions import _role
from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display  = ("name", "is_active_badge", "created_at")
    list_filter   = ("is_active",)
    search_fields = ("name",)

    def has_add_permission(self, request):
        return _role(request.user) == "MANAGER"

    def has_change_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    @admin.display(description="Faol")
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#27ae60;font-weight:700;">✓ Faol</span>')
        return format_html('<span style="color:#e74c3c;">✗ Nofaol</span>')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display    = ("category", "amount_display", "comment", "spent_at", "created_by", "created_at")
    list_filter     = ("category", "spent_at")
    search_fields   = ("comment",)
    readonly_fields = ("created_by", "created_at")
    date_hierarchy  = "spent_at"

    fieldsets = (
        ("Xarajat ma'lumotlari", {
            "fields": ("category", "amount", "comment", "spent_at")
        }),
        ("Tizim", {
            "fields": ("created_by", "created_at"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        return _role(request.user) == "MANAGER"

    def has_change_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def has_view_permission(self, request, obj=None):
        # Faqat MANAGER xarajatlarni ko'ra oladi
        return _role(request.user) == "MANAGER"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if _role(request.user) == "MANAGER":
            return qs
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="Miqdori")
    def amount_display(self, obj):
        return format_html('<strong style="color:#e74c3c;">{} so\'m</strong>', f"{obj.amount:,.0f}")
