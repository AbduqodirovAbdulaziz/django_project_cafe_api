from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from accounts.permissions import _role
from .models import Order, OrderItem, OrderStatusLog

STATUS_TRANSITIONS = {
    Order.Status.NEW:      [Order.Status.COOKING, Order.Status.CANCELED],
    Order.Status.COOKING:  [Order.Status.READY,   Order.Status.CANCELED],
    Order.Status.READY:    [Order.Status.SERVED,  Order.Status.CANCELED],
    Order.Status.SERVED:   [Order.Status.CANCELED],   # PAID yo'q — faqat to'lov orqali
    Order.Status.PAID:     [],
    Order.Status.CANCELED: [],
}

# Rol asosida qaysi statuslarga o'tish mumkin
ROLE_ALLOWED_TARGETS = {
    "MANAGER": {
        Order.Status.NEW:     [Order.Status.COOKING, Order.Status.CANCELED],
        Order.Status.COOKING: [Order.Status.READY,   Order.Status.CANCELED],
        Order.Status.READY:   [Order.Status.SERVED,  Order.Status.CANCELED],
        Order.Status.SERVED:  [Order.Status.CANCELED],
    },
    "CHEF": {
        Order.Status.NEW:     [Order.Status.COOKING],
        Order.Status.COOKING: [Order.Status.READY],
        Order.Status.READY:   [],
        Order.Status.SERVED:  [],
    },
    "WAITER": {
        Order.Status.NEW:     [Order.Status.CANCELED],
        Order.Status.COOKING: [],
        Order.Status.READY:   [Order.Status.SERVED],
        Order.Status.SERVED:  [],
    },
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
#  Order Admin forma
# ─────────────────────────────────────────────
class OrderAdminForm(forms.ModelForm):
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
            "placeholder": "Izohi (ixtiyoriy)...",
            "style": "max-width:400px;",
        }),
    )

    class Meta:
        model = Order
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        self._request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")

        if instance and instance.pk:
            role = _role(self._request.user) if self._request else "MANAGER"
            allowed = ROLE_ALLOWED_TARGETS.get(role, {}).get(instance.status, [])
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
    fields = ("menu_item", "qty", "notes", "item_name_snapshot", "unit_price_snapshot", "line_total")
    readonly_fields = ("item_name_snapshot", "unit_price_snapshot", "line_total")

    def has_add_permission(self, request, obj=None):
        if obj and obj.status in (Order.Status.PAID, Order.Status.CANCELED):
            return False
        role = _role(request.user)
        return role in ("MANAGER", "WAITER")

    def has_change_permission(self, request, obj=None):
        if obj and obj.status in (Order.Status.PAID, Order.Status.CANCELED):
            return False
        role = _role(request.user)
        return role in ("MANAGER", "WAITER")

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in (Order.Status.PAID, Order.Status.CANCELED):
            return False
        return _role(request.user) == "MANAGER"


# ─────────────────────────────────────────────
#  OrderStatusLog inline
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
    inlines = [OrderItemInline, OrderStatusLogInline]
    actions = ["action_bekor"]

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
                "⚠️ Ruxsat etilgan holat tanlang va «Saqlash» tugmasini bosing. "
                "PAID holati faqat to'lov orqali avtomatik o'rnatiladi.</span>"
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

    def get_form(self, request, obj=None, **kwargs):
        """Formaga request ni uzatamiz (rol tekshirish uchun)."""
        Form = super().get_form(request, obj, **kwargs)

        class FormWithRequest(Form):
            def __new__(cls, *args, **kwargs2):
                kwargs2["request"] = request
                return Form(*args, **kwargs2)

        # Agar bu OrderAdminForm bo'lsa, request ni uzatamiz
        if hasattr(Form, "_request") or Form.__name__ == "OrderAdminForm":
            return FormWithRequest
        return Form

    def get_fieldsets(self, request, obj=None):
        """Yangi order qo'shganda status bloki ko'rsatilmaydi."""
        if obj is None:
            role = _role(request.user)
            base_fields = (
                "order_type", "table",
                "customer_name", "customer_phone",
                "created_by", "notes",
            )
            if role == "MANAGER":
                return (
                    ("📋 Asosiy ma'lumotlar", {"fields": base_fields}),
                    ("💰 Chegirma", {"fields": ("discount_type", "discount_value")}),
                )
            else:
                return (
                    ("📋 Asosiy ma'lumotlar", {"fields": base_fields}),
                )
        return self.fieldsets

    def get_form(self, request, obj=None, **kwargs):
        """Forma classiga request uzatamiz."""
        kwargs["form"] = OrderAdminForm
        form_class = super().get_form(request, obj, **kwargs)

        original_init = form_class.__init__

        def new_init(self_form, *args, **kw):
            kw["request"] = request
            original_init(self_form, *args, **kw)

        form_class.__init__ = new_init
        return form_class

    def get_readonly_fields(self, request, obj=None):
        role = _role(request.user)
        readonly = list(self.readonly_fields)

        if role == "CHEF":
            # CHEF faqat ko'radi, hech narsani o'zgartira olmaydi
            all_fields = [f.name for f in Order._meta.get_fields() if hasattr(f, 'name')]
            return list(set(readonly + all_fields))

        if role == "WAITER":
            # WAITER discount/notes o'zgartira olmaydi (faqat status va o'z orderlari)
            readonly += ["discount_type", "discount_value", "order_type", "table",
                         "customer_name", "customer_phone", "created_by"]
        return readonly

    def has_add_permission(self, request):
        return _role(request.user) in ("MANAGER", "WAITER")

    def has_change_permission(self, request, obj=None):
        role = _role(request.user)
        if role == "MANAGER":
            return True
        if role == "WAITER":
            if obj is None:
                return True
            return obj.created_by_id == request.user.id
        if role == "CHEF":
            return True  # ko'rish uchun, lekin readonly_fields hamma narsani qoplaydi
        return False

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        role = _role(request.user)
        if role in ("MANAGER", "CHEF"):
            return qs
        if role == "WAITER":
            return qs.filter(created_by=request.user)
        return qs.none()

    # ── list_display metodlar ──
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

    # ── Saqlashda status o'zgartirish ──
    def save_model(self, request, obj, form, change):
        new_status = form.cleaned_data.get("new_status", "")
        comment    = form.cleaned_data.get("status_comment", "").strip()
        super().save_model(request, obj, form, change)

        if change and new_status:
            # PAID ga manual o'tish taqiqlangan
            if new_status == Order.Status.PAID:
                self.message_user(
                    request,
                    "❌ PAID holati faqat to'lov orqali avtomatik o'rnatiladi.",
                    messages.ERROR,
                )
                return

            role = _role(request.user)
            allowed = ROLE_ALLOWED_TARGETS.get(role, {}).get(obj.status, [])
            if new_status not in [s for s in allowed]:
                self.message_user(
                    request,
                    f"❌ {role} uchun bu status o'zgarishi ruxsat etilmagan.",
                    messages.ERROR,
                )
                return

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

    # ── Actions ──
    @admin.action(description="❌ BEKOR QILISH")
    def action_bekor(self, request, queryset):
        role = _role(request.user)
        for obj in queryset:
            if obj.status in (Order.Status.PAID, Order.Status.CANCELED):
                self.message_user(request, f"#{obj.id} allaqachon yopiq.", messages.WARNING)
                continue
            # WAITER faqat NEW statusidagi o'z buyurtmasini bekor qila oladi
            if role == "WAITER":
                if obj.created_by_id != request.user.id or obj.status != Order.Status.NEW:
                    self.message_user(
                        request,
                        f"#{obj.id}: WAITER faqat o'zining NEW holatdagi buyurtmasini bekor qila oladi.",
                        messages.ERROR,
                    )
                    continue
            try:
                obj.change_status(Order.Status.CANCELED, by_user=request.user, comment="Admin: bekor qilindi")
                self.message_user(request, f"✅ #{obj.id} bekor qilindi.", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"❌ #{obj.id}: {e}", messages.ERROR)


# ─────────────────────────────────────────────
#  OrderItem Admin
# ─────────────────────────────────────────────
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display    = ("order", "menu_item", "qty", "unit_price_snapshot", "line_total")
    search_fields   = ("item_name_snapshot", "order__order_code")
    readonly_fields = ("item_name_snapshot", "unit_price_snapshot", "line_total")

    def has_add_permission(self, request):
        return _role(request.user) in ("MANAGER", "WAITER")

    def has_change_permission(self, request, obj=None):
        return _role(request.user) in ("MANAGER", "WAITER")

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"


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

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    @admin.display(description="Dan")
    def from_uz(self, obj):
        return STATUS_UZ.get(obj.from_status, obj.from_status)

    @admin.display(description="Ga")
    def to_uz(self, obj):
        return STATUS_UZ.get(obj.to_status, obj.to_status)

    @admin.display(description="")
    def arrow(self, obj):
        return "→"
