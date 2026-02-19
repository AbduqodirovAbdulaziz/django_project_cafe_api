from django.contrib import admin
from django.utils.html import format_html

from accounts.permissions import _role
from .models import Category, MenuItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ("name", "sort_order", "is_active_badge", "created_at")
    list_editable = ("sort_order",)
    list_filter   = ("is_active",)
    search_fields = ("name",)
    ordering      = ("sort_order", "name")

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


class MenuItemInline(admin.TabularInline):
    model  = MenuItem
    extra  = 0
    fields = ("name", "price", "is_available", "prep_time_minutes")
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def has_change_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display   = ("name", "category", "price_display", "is_available_badge", "prep_time_minutes", "updated_at")
    list_filter    = ("category", "is_available")
    list_editable  = ()
    search_fields  = ("name", "description")
    ordering       = ("category__sort_order", "name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Asosiy", {
            "fields": ("category", "name", "price", "description", "image")
        }),
        ("Holat", {
            "fields": ("is_available", "prep_time_minutes")
        }),
        ("Vaqt", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        return _role(request.user) == "MANAGER"

    def has_change_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    def has_delete_permission(self, request, obj=None):
        return _role(request.user) == "MANAGER"

    @admin.display(description="Narxi")
    def price_display(self, obj):
        return format_html('<strong>{:,.0f} so\'m</strong>', obj.price)

    @admin.display(description="Mavjud")
    def is_available_badge(self, obj):
        if obj.is_available:
            return format_html('<span style="color:#27ae60;font-weight:700;">✓ Mavjud</span>')
        return format_html('<span style="color:#e74c3c;">✗ Mavjud emas</span>')
