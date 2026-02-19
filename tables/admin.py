from django.contrib import admin

from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display  = ("number", "status", "created_at")
    list_filter   = ("status",)
    search_fields = ("number",)
    readonly_fields = ("status",)  # Stol statusi faqat buyurtma orqali o'zgaradi
