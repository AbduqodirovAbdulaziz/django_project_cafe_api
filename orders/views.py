from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.permissions import IsManager, _role
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer, OrderCreateItemInputSerializer


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

        # WAITER faqat o'z buyurtmalarini ko'radi
        if role == "WAITER":
            qs = qs.filter(created_by=self.request.user)

        qp = self.request.query_params
        status_ = qp.get("status")
        table = qp.get("table")
        date_from = qp.get("date_from")
        date_to = qp.get("date_to")

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
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        if _role(request.user) == "CHEF":
            return Response(
                {"detail": "CHEF buyurtmani tahrir qila olmaydi."},
                status=http_status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if _role(request.user) == "CHEF":
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

    @action(detail=True, methods=["post"], url_path="add-item")
    def add_item(self, request, pk=None):
        role = _role(request.user)
        if role not in ("MANAGER", "WAITER"):
            return Response(
                {"detail": "Ruxsat yo'q."},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        order = self.get_object()

        # Serializer orqali validatsiya
        input_serializer = OrderCreateItemInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

        data = input_serializer.validated_data
        menu_item_id = data["menu_item_id"]
        qty = data["qty"]
        notes = data.get("notes", "")

        # MenuItem mavjudligini tekshirish
        from menu.models import MenuItem
        try:
            MenuItem.objects.get(pk=menu_item_id)
        except MenuItem.DoesNotExist:
            return Response(
                {"detail": f"MenuItem id={menu_item_id} topilmadi."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        item = OrderItem.objects.create(
            order=order,
            menu_item_id=menu_item_id,
            qty=qty,
            notes=notes,
        )
        order.recalculate_totals()
        return Response(
            OrderItemSerializer(item, context={"request": request}).data,
            status=http_status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="update-status")
    def update_status(self, request, pk=None):
        order = self.get_object()
        to_status = (request.data.get("to_status") or "").strip()
        comment = request.data.get("comment", "")

        if not to_status:
            return Response(
                {"detail": "to_status majburiy."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        role = _role(request.user)
        from_status = order.status
        allowed_by_role = set()

        if to_status == Order.Status.COOKING and from_status == Order.Status.NEW:
            allowed_by_role = {"MANAGER", "CHEF"}
        elif to_status == Order.Status.READY and from_status == Order.Status.COOKING:
            allowed_by_role = {"MANAGER", "CHEF"}
        elif to_status == Order.Status.SERVED and from_status == Order.Status.READY:
            allowed_by_role = {"MANAGER", "WAITER"}
        elif to_status == Order.Status.PAID and from_status == Order.Status.SERVED:
            allowed_by_role = {"MANAGER", "WAITER"}
        elif to_status == Order.Status.CANCELED:
            if from_status == Order.Status.NEW:
                allowed_by_role = {"MANAGER", "WAITER"}
            else:
                allowed_by_role = {"MANAGER"}

        if role not in allowed_by_role:
            return Response(
                {"detail": f"Ruxsat yo'q: {role} {from_status} -> {to_status}"},
                status=http_status.HTTP_403_FORBIDDEN,
            )

        try:
            order.change_status(
                to_status=to_status,
                by_user=request.user,
                comment=comment or "",
            )
        except (ValidationError, Exception) as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=http_status.HTTP_200_OK,
        )
