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
        # WAITER faqat o'z buyurtmalariga tegishli to'lovlarni ko'rsin
        if role == "WAITER":
            return qs.filter(order__created_by=self.request.user)
        # CHEF ko'rmasin
        return qs.none()

    def create(self, request, *args, **kwargs):
        role = _role(request.user)
        if role not in ("MANAGER", "WAITER"):
            return Response(
                {"detail": "Ruxsat yo'q."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = serializer.validated_data.get("order")
        if role == "WAITER" and order:
            if order.created_by_id != request.user.id:
                return Response(
                    {"detail": "Bu buyurtma sizga tegishli emas."},
                    status=http_status.HTTP_403_FORBIDDEN,
                )

        payment = serializer.save(received_by=request.user)

        # SERVED + due=0 bo'lsa avtomatik PAID ga o'tkazamiz
        order = payment.order
        order.refresh_from_db()
        if order.status == Order.Status.SERVED and order.due_amount == 0:
            try:
                order.change_status(
                    Order.Status.PAID,
                    by_user=request.user,
                    comment="Auto: payment complete",
                )
            except Exception:
                pass

        return Response(
            PaymentSerializer(payment, context={"request": request}).data,
            status=http_status.HTTP_201_CREATED,
        )
