from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display    = ("order", "jami_summa", "qoldiq", "method", "amount", "is_debt", "received_by", "paid_at")
    list_filter     = ("method", "is_debt", "paid_at")
    search_fields   = ("order__order_code",)
    readonly_fields = ("order_malumot", "jami_summa_info", "qoldiq_info", "received_by", "paid_at")
    fields          = (
        "order", "order_malumot", "jami_summa_info", "qoldiq_info",
        "method", "amount", "is_debt", "debt_note",
        "received_by", "paid_at",
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.received_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return qs
        if hasattr(request.user, "role") and request.user.role == "WAITER":
            return qs.filter(order__created_by=request.user)
        return qs.none()

    @admin.display(description="Jami summa")
    def jami_summa(self, obj):
        return f"{obj.order.total:,.2f} so'm"

    @admin.display(description="Qoldiq")
    def qoldiq(self, obj):
        return f"{obj.order.due_amount:,.2f} so'm"

    @admin.display(description="Buyurtma ma'lumoti")
    def order_malumot(self, obj):
        return f"#{obj.order.order_code} — {obj.order.get_order_type_display()}"

    @admin.display(description="Jami summa")
    def jami_summa_info(self, obj):
        return f"{obj.order.total:,.2f} so'm"

    @admin.display(description="Qoldiq")
    def qoldiq_info(self, obj):
        return f"{obj.order.due_amount:,.2f} so'm"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("order",)
        return self.readonly_fields
