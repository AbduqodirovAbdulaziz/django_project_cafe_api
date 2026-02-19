from rest_framework import serializers
from .models import Table


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ["id", "number", "status", "created_at", "updated_at"]
        # status faqat Order orqali o'zgaradi, API orqali to'g'ridan-to'g'ri o'zgartirish mumkin emas
        read_only_fields = ["status", "created_at", "updated_at"]
