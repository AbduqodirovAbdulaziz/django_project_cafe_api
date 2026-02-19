from rest_framework import serializers
from .models import ExpenseCategory, Expense


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "name", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    category_name = serializers.CharField(
        source="category.name", read_only=True
    )

    class Meta:
        model = Expense
        fields = [
            "id", "category", "category_name",
            "amount", "comment", "spent_at",
            "created_by", "created_by_username", "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]
