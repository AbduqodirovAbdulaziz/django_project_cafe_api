from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.permissions import _role
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, OrderCreateItemInputSerializer

# ─────────────────────────────────────────────────────────────
#  Rol asosida qaysi statusga kim o'ta olishi — MARKAZIY QOIDA
# ─────────────────────────────────────────────────────────────
#  MUHIM: SERVED → PAID yo'q! PAID faqat to'lov orqali avtomatik.
STATUS_TRANSITION_ROLES = {
    # (from_status, to_status): {rollar seti}
    (Order.Status.NEW,     Order.Status.COOKING):  {"MANAGER", "CHEF"},
    (Order.Status.COOKING, Order.Status.READY):    {"MANAGER", "CHEF"},
    (Order.Status.READY,   Order.Status.SERVED):   {"MANAGER", "WAITER"},
    # CANCELED — kimlar qila oladi:
    (Order.Status.NEW,     Order.Status.CANCELED): {"MANAGER", "WAITER"},
    (Order.Status.COOKING, Order.Status.CANCELED): {"MANAGER"},
    (Order.Status.READY,   Order.Status.CANCELED): {"MANAGER"},
    (Order.Status.SERVED,  Order.Status.CANCELED): {"MANAGER"},
}

class OrderViewSet(ModelViewSet):
    queryset = Order.objects.select_related(
        "table", "created_by"
    ).prefetch_related("items", "status_logs").all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ["created_at", "total", "status", "id"]
    search_fields = ["order_code", "customer_name", "customer_phone", "notes"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = _role(self.request.user)

        # CHEF hamma buyurtmani ko'radi (oshxonada ishlashi uchun)
        # WAITER faqat o'z buyurtmalarini ko'radi
        if role == "WAITER":
            qs = qs.filter(created_by=self.request.user)

        qp = self.request.query_params
        status_ = qp.get("status")
        table   = qp.get("table")
        date_from = qp.get("date_from")
        date_to   = qp.get("date_to")

        if status_:
            qs = qs.filter(status=status_)
        if table:
            qs = qs.filter(table_id=table)
        if date_from:
            d1 = parse_date(date_from)
            if d1:
                qs = qs.filter(created_at__date__gte=d1)
        if date_to:
            d2 = parse_date(date_to)
            if d2:
                qs = qs.filter(created_at__date__lte=d2)

        return qs

    def perform_create(self, serializer):
        role = _role(self.request.user)
        if role not in ("MANAGER", "WAITER"):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Faqat MANAGER yoki WAITER buyurtma yarata oladi.")
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        role = _role(request.user)
        if role == "CHEF":
            return Response(
                {"detail": "CHEF buyurtmani tahrir qila olmaydi."},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        role = _role(request.user)
        if role == "CHEF":
            return Response(
                {"detail": "CHEF buyurtmani tahrir qila olmaydi."},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if _role(request.user) != "MANAGER":
            return Response(
                {"detail": "Faqat MANAGER o'chira oladi."},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    # ── Element qo'shish ──
    @action(detail=True, methods=["post"], url_path="add-item")
    def add_item(self, request, pk=None):
        role = _role(request.user)
        if role not in ("MANAGER", "WAITER"):
            return Response({"detail": "Ruxsat yo'q."}, status=http_status.HTTP_403_FORBIDDEN)

        order = self.get_object()

        # WAITER faqat o'z buyurtmasiga element qo'sha oladi
        if role == "WAITER" and order.created_by_id != request.user.id:
            return Response(
                {"detail": "Bu buyurtma sizga tegishli emas."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        # Yopiq buyurtmaga element qo'shib bo'lmaydi
        if order.status in (Order.Status.PAID, Order.Status.CANCELED):
            return Response(
                {"detail": "Yopiq buyurtmaga element qo'shib bo'lmaydi."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        input_ser = OrderCreateItemInputSerializer(data=request.data)
        if not input_ser.is_valid():
            return Response(input_ser.errors, status=http_status.HTTP_400_BAD_REQUEST)

        data = input_ser.validated_data
        item = OrderItem.objects.create(
            order=order,
            menu_item_id=data["menu_item_id"],
            qty=data["qty"],
            notes=data.get("notes", ""),
        )
        order.recalculate_totals()
        return Response(
            OrderItemSerializer(item, context={"request": request}).data,
            status=http_status.HTTP_201_CREATED,
        )

    # ── Status o'zgartirish ──
    @action(detail=True, methods=["post"], url_path="update-status")
    def update_status(self, request, pk=None):
        order     = self.get_object()
        to_status = (request.data.get("to_status") or "").strip()
        comment   = request.data.get("comment", "")

        if not to_status:
            return Response({"detail": "to_status majburiy."}, status=http_status.HTTP_400_BAD_REQUEST)

        # PAID ga manual o'tish taqiqlangan — faqat to'lov orqali avtomatik
        if to_status == Order.Status.PAID:
            return Response(
                {"detail": "PAID statusi faqat to'lov to'liq qilingandan keyin avtomatik o'rnatiladi."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        role        = _role(request.user)
        from_status = order.status
        key         = (from_status, to_status)
        allowed_roles = STATUS_TRANSITION_ROLES.get(key, set())

        if role not in allowed_roles:
            return Response(
                {"detail": f"Ruxsat yo'q: {role} — {from_status} → {to_status}"},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        # WAITER faqat o'z buyurtmasini o'zgartira oladi
        if role == "WAITER" and order.created_by_id != request.user.id:
            return Response(
                {"detail": "Bu buyurtma sizga tegishli emas."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        try:
            order.change_status(to_status=to_status, by_user=request.user, comment=comment)
        except (ValidationError, Exception) as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=http_status.HTTP_200_OK,
        )

    # ── WAITER statistikasi ──
    @action(detail=False, methods=["get"], url_path="my-stats")
    def my_stats(self, request):
        """Waiter o'z buyurtmalarining qisqa statistikasini ko'radi."""
        from django.db.models import Count, Sum
        role = _role(request.user)
        if role not in ("MANAGER", "WAITER"):
            return Response({"detail": "Ruxsat yo'q."}, status=http_status.HTTP_403_FORBIDDEN)

        qs = Order.objects.filter(created_by=request.user)

        date_from = parse_date(request.query_params.get("date_from", ""))
        date_to   = parse_date(request.query_params.get("date_to", ""))
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        total_orders  = qs.count()
        by_status     = qs.values("status").annotate(count=Count("id"))
        total_revenue = qs.filter(status=Order.Status.PAID).aggregate(s=Sum("total"))["s"] or 0

        return Response({
            "total_orders": total_orders,
            "by_status": list(by_status),
            "total_revenue_paid": total_revenue,
        })
