from django.contrib import admin

from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display  = ("name", "is_active", "created_at")
    list_editable = ("is_active",)
    search_fields = ("name",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display  = ("category", "amount", "spent_at", "created_by", "created_at")
    list_filter   = ("category", "spent_at")
    search_fields = ("comment",)
    readonly_fields = ("created_by", "created_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return qs
        if hasattr(request.user, "role") and request.user.role == "WAITER":
            return qs.filter(created_by=request.user)
        return qs.none()
