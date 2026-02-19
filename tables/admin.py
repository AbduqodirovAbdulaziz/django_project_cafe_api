from django.contrib import admin
from django.utils.html import format_html

from accounts.permissions import _role
from orders.models import Order
from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display    = ("number", "status_badge", "faol_buyurtmalar", "created_at")
    list_filter     = ("status",)
    search_fields   = ("number",)
    readonly_fields = ("status", "created_at", "updated_at")

    fieldsets = (
        ("Stol ma'lumotlari", {
            "fields": ("number", "status")
        }),
        ("Vaqt", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        return _role(request.user) == "MANAGER"

    def has_change_permission(self, request, obj=None):
        # Faqat MANAGER stol raqamini o'zgartira oladi
        # Status faqat buyurtma orqali o'zgaradi (readonly)
        return _role(request.user) == "MANAGER"

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    @admin.display(description="Holati")
    def status_badge(self, obj):
        if obj.status == Table.Status.FREE:
            return format_html(
                '<span style="background:#27ae60;color:#fff;padding:3px 10px;'
                'border-radius:12px;font-size:.82rem;font-weight:600;">🟢 Bo\'sh</span>'
            )
        return format_html(
            '<span style="background:#e74c3c;color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:.82rem;font-weight:600;">🔴 Band</span>'
        )

    @admin.display(description="Faol buyurtmalar")
    def faol_buyurtmalar(self, obj):
        count = Order.objects.filter(
            table=obj,
            status__in=[
                Order.Status.NEW,
                Order.Status.COOKING,
                Order.Status.READY,
                Order.Status.SERVED,
            ]
        ).count()
        if count:
            return format_html(
                '<span style="color:#e67e22;font-weight:700;">{} ta buyurtma</span>', count
            )
        return format_html('<span style="color:#95a5a6;">—</span>')
