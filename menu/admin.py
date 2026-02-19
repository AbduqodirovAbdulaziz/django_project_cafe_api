from django.contrib import admin

from .models import Category, MenuItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ("name", "sort_order", "is_active", "created_at")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name",)
    ordering      = ("sort_order", "name")

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display  = ("name", "category", "price", "is_available", "prep_time_minutes")
    list_editable = ("is_available",)
    list_filter   = ("category", "is_available")
    search_fields = ("name", "description")

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff
