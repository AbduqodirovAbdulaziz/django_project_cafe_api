from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    received_by_username = serializers.CharField(
        source="received_by.username", read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id", "order", "received_by", "received_by_username",
            "method", "amount", "is_debt", "debt_note", "paid_at",
        ]
        read_only_fields = ["received_by", "paid_at"]
