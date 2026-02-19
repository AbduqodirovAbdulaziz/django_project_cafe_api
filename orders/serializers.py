from rest_framework import serializers
from django.db import transaction
from menu.models import MenuItem
from .models import Order, OrderItem, OrderStatusLog


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id", "menu_item", "menu_item_name",
            "item_name_snapshot", "unit_price_snapshot",
            "qty", "notes", "line_total", "created_at",
        ]
        read_only_fields = ["item_name_snapshot", "unit_price_snapshot", "line_total", "created_at"]


class OrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source="changed_by.username", read_only=True)

    class Meta:
        model = OrderStatusLog
        fields = ["id", "from_status", "to_status", "changed_by", "changed_by_username", "changed_at", "comment"]
        read_only_fields = ["changed_at"]


class OrderCreateItemInputSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_menu_item_id(self, value):
        if not MenuItem.objects.filter(pk=value).exists():
            raise serializers.ValidationError(f"MenuItem id={value} topilmadi.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    # create payload uchun (ixtiyoriy)
    create_items = OrderCreateItemInputSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_code",
            "order_type", "table", "customer_name", "customer_phone",
            "created_by", "created_by_username",
            "status", "notes",
            "discount_type", "discount_value",
            "subtotal", "discount_amount", "total", "paid_total", "due_amount",
            "is_closed",
            "created_at", "updated_at",
            "items", "status_logs",
            "create_items",
        ]
        read_only_fields = [
            "order_code",
            "created_by",
            "subtotal", "discount_amount", "total", "paid_total", "due_amount",
            "is_closed",
            "created_at", "updated_at",
        ]

    def validate(self, attrs):
        order_type = attrs.get("order_type", getattr(self.instance, "order_type", None))
        table = attrs.get("table", getattr(self.instance, "table", None))
        customer_name = attrs.get("customer_name", getattr(self.instance, "customer_name", "")) or ""

        if order_type == Order.OrderType.DINE_IN and not table:
            raise serializers.ValidationError({"table": "DINE_IN uchun table majburiy."})
        if order_type == Order.OrderType.TAKEAWAY and not customer_name.strip():
            raise serializers.ValidationError({"customer_name": "TAKEAWAY uchun customer_name majburiy."})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("create_items", [])
        order = Order.objects.create(**validated_data)
        for it in items_data:
            OrderItem.objects.create(
                order=order,
                menu_item_id=it["menu_item_id"],
                qty=it["qty"],
                notes=it.get("notes", ""),
            )
        order.recalculate_totals()
        return order
