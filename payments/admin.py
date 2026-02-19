from decimal import Decimal

from django.contrib import admin, messages
from django.utils.html import format_html

from accounts.permissions import _role
from orders.models import Order
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    class Media:
        js = ("payments/js/payment_order_info.js",)

    list_display    = ("order", "order_holati", "jami_summa", "qoldiq", "method", "amount", "is_debt", "received_by", "paid_at")
    list_filter     = ("method", "is_debt", "paid_at")
    search_fields   = ("order__order_code",)
    readonly_fields = ("order_malumot", "order_holati_info", "jami_summa_info", "qoldiq_info", "received_by", "paid_at")

    fields = (
        "order", "order_malumot", "order_holati_info",
        "jami_summa_info", "qoldiq_info",
        "method", "amount", "is_debt", "debt_note",
        "received_by", "paid_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        role = _role(request.user)
        if role == "MANAGER":
            return qs
        if role == "WAITER":
            return qs.filter(order__created_by=request.user)
        return qs.none()

    def has_add_permission(self, request):
        return _role(request.user) in ("MANAGER", "WAITER")

    def has_change_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("order",)
        return self.readonly_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "order":
            # Faqat SERVED holatdagi buyurtmalarni ko'rsatamiz
            kwargs["queryset"] = Order.objects.filter(status=Order.Status.SERVED)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        role = _role(request.user)

        if not change:
            # Yangi to'lov tekshirishlari
            if not obj.order:
                self.message_user(request, "❌ Buyurtma tanlanishi shart.", messages.ERROR)
                return

            if obj.order.status != Order.Status.SERVED:
                self.message_user(
                    request,
                    f"❌ To'lov faqat SERVED holatdagi buyurtmaga qo'shiladi. Hozirgi holat: {obj.order.status}",
                    messages.ERROR,
                )
                return

            # WAITER faqat o'z buyurtmasiga to'lov qabul qila oladi
            if role == "WAITER" and obj.order.created_by_id != request.user.id:
                self.message_user(request, "❌ Bu buyurtma sizga tegishli emas.", messages.ERROR)
                return

            obj.received_by = request.user

        super().save_model(request, obj, form, change)

        # To'liq to'langan bo'lsa PAID ga o'tkazish
        if not change and obj.order:
            order = obj.order
            order.refresh_from_db()
            if order.status == Order.Status.SERVED and order.due_amount <= Decimal("0.00"):
                try:
                    order.change_status(
                        Order.Status.PAID,
                        by_user=request.user,
                        comment="Avtomatik: to'lov to'liq amalga oshirildi (admin)",
                    )
                    self.message_user(
                        request,
                        "✅ To'lov qabul qilindi va buyurtma PAID ga o'tkazildi!",
                        messages.SUCCESS,
                    )
                except Exception as e:
                    self.message_user(request, f"⚠️ Status o'zgarmadi: {e}", messages.WARNING)
            else:
                order.refresh_from_db()
                self.message_user(
                    request,
                    f"✅ To'lov qabul qilindi. Qoldiq: {order.due_amount:,.0f} so'm",
                    messages.SUCCESS,
                )

    # ── Display metodlar ──
    @admin.display(description="Buyurtma holati")
    def order_holati(self, obj):
        if not obj.order: return "—"
        colors = {
            "SERVED": "#8e44ad", "PAID": "#16a085",
        }
        color = colors.get(obj.order.status, "#999")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:.8rem;">{}</span>',
            color, obj.order.get_status_display()
        )

    @admin.display(description="Jami summa")
    def jami_summa(self, obj):
        return f"{obj.order.total:,.0f} so'm" if obj.order else "0 so'm"

    @admin.display(description="Qoldiq")
    def qoldiq(self, obj):
        if obj.order and obj.order.due_amount > 0:
            return format_html(
                '<span style="color:#e74c3c;font-weight:700;">{} so\'m</span>',
                f"{obj.order.due_amount:,.0f}"
            )
        return format_html('<span style="color:#27ae60;">✓ To\'liq</span>')

    @admin.display(description="Buyurtma ma'lumoti")
    def order_malumot(self, obj):
        if not obj.order: return "—"
        return f"#{obj.order.order_code} — {obj.order.get_order_type_display()}"

    @admin.display(description="Buyurtma holati")
    def order_holati_info(self, obj):
        return obj.order.get_status_display() if obj.order else "—"

    @admin.display(description="Jami summa")
    def jami_summa_info(self, obj):
        return f"{obj.order.total:,.0f} so'm" if obj.order else "0 so'm"

    @admin.display(description="Qoldiq")
    def qoldiq_info(self, obj):
        return f"{obj.order.due_amount:,.0f} so'm" if obj.order else "0 so'm"
