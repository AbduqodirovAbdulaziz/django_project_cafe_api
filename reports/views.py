from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from django.db.models import Sum, Count

from accounts.permissions import IsManager, _role
from payments.models import Payment
from expenses.models import Expense
from orders.models import Order, OrderItem


class DailyReportView(APIView):
    """Kunlik hisobot — faqat MANAGER."""
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        date_str = request.query_params.get("date")
        d = parse_date(date_str) if date_str else None
        if not d:
            return Response({"detail": "date=YYYY-MM-DD majburiy."}, status=400)

        revenue = Payment.objects.filter(is_debt=False, paid_at__date=d).aggregate(s=Sum("amount"))["s"] or 0
        expense = Expense.objects.filter(spent_at__date=d).aggregate(s=Sum("amount"))["s"] or 0
        profit  = revenue - expense

        top_items = (
            OrderItem.objects.filter(created_at__date=d)
            .values("item_name_snapshot")
            .annotate(qty=Sum("qty"), amount=Sum("line_total"))
            .order_by("-qty")[:10]
        )

        orders_by_status = (
            Order.objects.filter(created_at__date=d)
            .values("status")
            .annotate(count=Count("id"))
        )

        return Response({
            "date": str(d),
            "revenue": revenue,
            "expense": expense,
            "profit": profit,
            "top_items": list(top_items),
            "orders_by_status": list(orders_by_status),
        })


class RangeReportView(APIView):
    """Davr bo'yicha hisobot — faqat MANAGER."""
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        df = parse_date(request.query_params.get("date_from", ""))
        dt = parse_date(request.query_params.get("date_to", ""))
        if not df or not dt:
            return Response({"detail": "date_from va date_to majburiy."}, status=400)

        revenue = Payment.objects.filter(
            is_debt=False, paid_at__date__gte=df, paid_at__date__lte=dt
        ).aggregate(s=Sum("amount"))["s"] or 0

        expense = Expense.objects.filter(
            spent_at__date__gte=df, spent_at__date__lte=dt
        ).aggregate(s=Sum("amount"))["s"] or 0

        profit = revenue - expense

        top_items = (
            OrderItem.objects.filter(created_at__date__gte=df, created_at__date__lte=dt)
            .values("item_name_snapshot")
            .annotate(qty=Sum("qty"), amount=Sum("line_total"))
            .order_by("-qty")[:20]
        )

        orders_by_status = (
            Order.objects.filter(created_at__date__gte=df, created_at__date__lte=dt)
            .values("status")
            .annotate(count=Count("id"))
        )

        return Response({
            "date_from": str(df),
            "date_to": str(dt),
            "revenue": revenue,
            "expense": expense,
            "profit": profit,
            "top_items": list(top_items),
            "orders_by_status": list(orders_by_status),
        })


class WaiterStatsView(APIView):
    """Ofitsiant o'z statistikasini ko'radi."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = _role(request.user)
        if role not in ("MANAGER", "WAITER"):
            return Response({"detail": "Ruxsat yo'q."}, status=403)

        # Manager boshqa ofitsiantning statsini ko'rishi mumkin
        user_id = request.query_params.get("user_id")
        if role == "MANAGER" and user_id:
            from accounts.models import User
            try:
                target_user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response({"detail": "Foydalanuvchi topilmadi."}, status=404)
        else:
            target_user = request.user

        df = parse_date(request.query_params.get("date_from", ""))
        dt = parse_date(request.query_params.get("date_to", ""))

        qs = Order.objects.filter(created_by=target_user)
        if df:
            qs = qs.filter(created_at__date__gte=df)
        if dt:
            qs = qs.filter(created_at__date__lte=dt)

        total_orders     = qs.count()
        by_status        = list(qs.values("status").annotate(count=Count("id")))
        total_revenue    = qs.filter(status=Order.Status.PAID).aggregate(s=Sum("total"))["s"] or 0
        payments_received = Payment.objects.filter(received_by=target_user)
        if df:
            payments_received = payments_received.filter(paid_at__date__gte=df)
        if dt:
            payments_received = payments_received.filter(paid_at__date__lte=dt)

        total_payments = payments_received.aggregate(s=Sum("amount"))["s"] or 0

        return Response({
            "user": target_user.username,
            "role": target_user.role,
            "total_orders": total_orders,
            "by_status": by_status,
            "total_revenue_paid_orders": total_revenue,
            "total_payments_received": total_payments,
        })
