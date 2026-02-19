from decimal import Decimal

from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.permissions import _role
from orders.models import Order
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.select_related("order", "received_by").all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ["paid_at", "amount", "id"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = _role(self.request.user)
        if role == "MANAGER":
            return qs
        if role == "WAITER":
            # WAITER faqat o'z buyurtmalariga tegishli to'lovlarni ko'radi
            return qs.filter(order__created_by=self.request.user)
        # CHEF to'lovlarni ko'ra olmaydi
        return qs.none()

    def create(self, request, *args, **kwargs):
        role = _role(request.user)
        if role not in ("MANAGER", "WAITER"):
            return Response(
                {"detail": "Faqat MANAGER yoki WAITER to'lov qabul qila oladi."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.validated_data.get("order")

        # WAITER faqat o'z buyurtmasiga to'lov qabul qila oladi
        if role == "WAITER" and order:
            if order.created_by_id != request.user.id:
                return Response(
                    {"detail": "Bu buyurtma sizga tegishli emas."},
                    status=http_status.HTTP_403_FORBIDDEN,
                )

        # To'lov qabul qilish uchun buyurtma SERVED bo'lishi shart
        if order and order.status != Order.Status.SERVED:
            return Response(
                {"detail": f"To'lov faqat SERVED holatdagi buyurtmaga qo'shiladi. Hozirgi holat: {order.status}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        payment = serializer.save(received_by=request.user)

        # To'lov saqlangandan keyin buyurtmani yangilash
        order = payment.order
        order.refresh_from_db()

        # due_amount == 0 bo'lsa avtomatik PAID
        if order.status == Order.Status.SERVED and order.due_amount <= Decimal("0.00"):
            try:
                order.change_status(
                    Order.Status.PAID,
                    by_user=request.user,
                    comment="Avtomatik: to'lov to'liq amalga oshirildi",
                )
            except Exception:
                pass

        return Response(
            PaymentSerializer(payment, context={"request": request}).data,
            status=http_status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """To'lovni o'zgartirish — faqat MANAGER."""
        if _role(request.user) != "MANAGER":
            return Response(
                {"detail": "To'lovni faqat MANAGER o'zgartira oladi."},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if _role(request.user) != "MANAGER":
            return Response(
                {"detail": "To'lovni faqat MANAGER o'zgartira oladi."},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """To'lovni o'chirish — faqat MANAGER."""
        if _role(request.user) != "MANAGER":
            return Response(
                {"detail": "To'lovni faqat MANAGER o'chira oladi."},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)
