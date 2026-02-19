from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import Order, OrderItem, OrderStatusLog

STATUS_TRANSITIONS = {
    Order.Status.NEW:      [Order.Status.COOKING, Order.Status.CANCELED],
    Order.Status.COOKING:  [Order.Status.READY,   Order.Status.CANCELED],
    Order.Status.READY:    [Order.Status.SERVED,  Order.Status.CANCELED],
    Order.Status.SERVED:   [Order.Status.PAID,    Order.Status.CANCELED],
    Order.Status.PAID:     [],
    Order.Status.CANCELED: [],
}

STATUS_UZ = {
    "NEW":      "🆕 Yangi",
    "COOKING":  "👨‍🍳 Tayyorlanmoqda",
    "READY":    "✅ Tayyor",
    "SERVED":   "🍽️ Berildi",
    "PAID":     "💰 To'landi",
    "CANCELED": "❌ Bekor qilindi",
}

STATUS_COLORS = {
    "NEW":      "#3498db",
    "COOKING":  "#e67e22",
    "READY":    "#27ae60",
    "SERVED":   "#8e44ad",
    "PAID":     "#16a085",
    "CANCELED": "#e74c3c",
}


# ─────────────────────────────────────────────
#  Order Admin forma — status dropdown qo'shilgan
# ─────────────────────────────────────────────
class OrderAdminForm(forms.ModelForm):
    """
    Status o'zgartirish uchun: faqat ruxsat etilgan
    statuslarni dropdown sifatida ko'rsatadi.
    """
    new_status = forms.ChoiceField(
        label="Holatni o'zgartirish",
        choices=[("", "— o'zgartirmaslik —")],
        required=False,
        widget=forms.Select(attrs={"class": "form-control", "style": "max-width:280px;"}),
    )
    status_comment = forms.CharField(
        label="O'zgartirish izohi",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Masalan: mijoz so'radi, oshpaz tayyor dedi...",
            "style": "max-width:400px;",
        }),
    )

    class Meta:
        model = Order
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance and instance.pk:
            allowed = STATUS_TRANSITIONS.get(instance.status, [])
            self.fields["new_status"].choices = (
                [("", f"— o'zgartirmaslik ({STATUS_UZ.get(instance.status, instance.status)}) —")]
                + [(s, STATUS_UZ.get(s, s)) for s in allowed]
            )
        else:
            self.fields.pop("new_status", None)
            self.fields.pop("status_comment", None)


# ─────────────────────────────────────────────
#  OrderItem inline
# ─────────────────────────────────────────────
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ("menu_item", "qty", "notes",
              "item_name_snapshot", "unit_price_snapshot", "line_total")
    readonly_fields = ("item_name_snapshot", "unit_price_snapshot", "line_total")


# ─────────────────────────────────────────────
#  OrderStatusLog inline — faqat ko'rish
# ─────────────────────────────────────────────
class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    can_delete = False
    readonly_fields = ("from_status_uz", "to_status_uz", "changed_by", "changed_at", "comment")
    fields = ("from_status_uz", "to_status_uz", "changed_by", "changed_at", "comment")
    verbose_name = "Status tarixi"
    verbose_name_plural = "Status tarixi"

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Dan")
    def from_status_uz(self, obj):
        return STATUS_UZ.get(obj.from_status, obj.from_status)

    @admin.display(description="Ga")
    def to_status_uz(self, obj):
        return STATUS_UZ.get(obj.to_status, obj.to_status)



# ─────────────────────────────────────────────
#  OrderAdmin
# ─────────────────────────────────────────────
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form    = OrderAdminForm
    inlines = [OrderItemInline, OrderStatusLogInline]
    actions = ["action_tolandi", "action_bekor"]

    list_display  = (
        "id", "order_code", "turi", "holati_badge",
        "table", "total_display", "paid_total", "due_display", "created_at",
    )
    list_filter   = ("order_type", "status", "created_at")
    search_fields = ("order_code", "customer_name", "customer_phone")

    readonly_fields = (
        "order_code", "holati_badge",
        "subtotal", "discount_amount",
        "total", "paid_total", "due_amount",
        "created_at", "updated_at",
    )

    fieldsets = (
        ("📋 Asosiy ma'lumotlar", {
            "fields": (
                "order_code", "order_type", "table",
                "customer_name", "customer_phone",
                "created_by", "notes",
            )
        }),
        ("🔄 Holatni o'zgartirish", {
            "fields": ("holati_badge", "new_status", "status_comment"),
            "description": (
                "<span style='color:#856404;font-weight:600;'>"
                "⚠️ Yangi holat tanlang va «Saqlash» tugmasini bosing.</span>"
            ),
        }),
        ("💰 Hisob-kitob", {
            "fields": (
                "discount_type", "discount_value",
                "subtotal", "discount_amount",
                "total", "paid_total", "due_amount",
            ),
        }),
        ("🕐 Vaqt", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ── list_display uchun ko'rinish metodlari ──
    @admin.display(description="Turi")
    def turi(self, obj):
        return obj.get_order_type_display()

    @admin.display(description="Holati")
    def holati_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#999")
        label = STATUS_UZ.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:.82rem;font-weight:600;">{}</span>',
            color, label
        )
    holati_badge.short_description = "Holati"

    @admin.display(description="Jami")
    def total_display(self, obj):
        return f"{obj.total:,.0f} so'm"

    @admin.display(description="Qoldiq")
    def due_display(self, obj):
        if obj.due_amount > 0:
            return format_html(
                '<span style="color:#e74c3c;font-weight:700;">{} so\'m</span>',
                f"{obj.due_amount:,.0f}"
            )
        return format_html('<span style="color:#27ae60;">✓ To\'liq</span>')

    # ── Queryset ──
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff:
            return qs
        if hasattr(request.user, "role") and request.user.role == "WAITER":
            return qs.filter(created_by=request.user)
        return qs.none()

    # ── Saqlashda status o'zgartirish ──
    def save_model(self, request, obj, form, change):
        new_status = form.cleaned_data.get("new_status", "")
        comment    = form.cleaned_data.get("status_comment", "").strip()

        # Avval obyektni saqlaymiz
        super().save_model(request, obj, form, change)

        # Keyin status o'zgartirish (agar tanlangan bo'lsa)
        if change and new_status:
            try:
                obj.refresh_from_db()
                obj.change_status(
                    to_status=new_status,
                    by_user=request.user,
                    comment=comment or f"Admin: {STATUS_UZ.get(new_status, new_status)}",
                )
                self.message_user(
                    request,
                    f"✅ Holat «{STATUS_UZ.get(new_status, new_status)}» ga o'zgartirildi.",
                    messages.SUCCESS,
                )
            except (ValidationError, Exception) as e:
                self.message_user(request, f"❌ Status xatosi: {e}", messages.ERROR)

    # ── Ro'yxat sahifasidagi action lar ──
    @admin.action(description="💰 TO'LANDI deb belgilash")
    def action_tolandi(self, request, queryset):
        for obj in queryset:
            try:
                obj.change_status(
                    Order.Status.PAID,
                    by_user=request.user,
                    comment="Admin: to'landi",
                )
                self.message_user(request, f"✅ #{obj.id} to'landi.", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"❌ #{obj.id}: {e}", messages.ERROR)

    @admin.action(description="❌ BEKOR QILISH")
    def action_bekor(self, request, queryset):
        for obj in queryset:
            try:
                obj.change_status(
                    Order.Status.CANCELED,
                    by_user=request.user,
                    comment="Admin: bekor qilindi",
                )
                self.message_user(request, f"✅ #{obj.id} bekor qilindi.", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"❌ #{obj.id}: {e}", messages.ERROR)



# ─────────────────────────────────────────────
#  OrderItem
# ─────────────────────────────────────────────
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display    = ("order", "menu_item", "qty", "unit_price_snapshot", "line_total")
    search_fields   = ("item_name_snapshot", "order__order_code")
    readonly_fields = ("item_name_snapshot", "unit_price_snapshot", "line_total")


# ─────────────────────────────────────────────
#  OrderStatusLog — faqat ko'rish
# ─────────────────────────────────────────────
@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display    = ("order", "from_uz", "arrow", "to_uz", "changed_by", "changed_at")
    list_filter     = ("from_status", "to_status", "changed_at")
    search_fields   = ("order__order_code", "comment")
    readonly_fields = ("order", "from_status", "to_status", "changed_by", "changed_at", "comment")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Dan")
    def from_uz(self, obj):
        return STATUS_UZ.get(obj.from_status, obj.from_status)

    @admin.display(description="Ga")
    def to_uz(self, obj):
        return STATUS_UZ.get(obj.to_status, obj.to_status)

    @admin.display(description="")
    def arrow(self, obj):
        return "→"
