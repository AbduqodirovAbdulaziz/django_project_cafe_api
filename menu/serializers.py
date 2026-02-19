from rest_framework import serializers
from .models import Category, MenuItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "sort_order", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            "id", "category", "category_name",
            "name", "price", "description",
            "image", "image_url",
            "is_available", "prep_time_minutes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "image_url"]

    def get_image_url(self, obj) -> str | None:
        request = self.context.get("request")
        if not obj.image:
            return None
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url
