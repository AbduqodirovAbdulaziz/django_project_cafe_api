from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from django.db.models import Sum

from accounts.permissions import IsManager
from payments.models import Payment
from expenses.models import Expense
from orders.models import OrderItem


class DailyReportView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        date_str = request.query_params.get("date")
        d = parse_date(date_str) if date_str else None
        if not d:
            return Response({"detail": "date=YYYY-MM-DD majburiy."}, status=400)

        revenue = Payment.objects.filter(is_debt=False, paid_at__date=d).aggregate(s=Sum("amount"))["s"] or 0
        expense = Expense.objects.filter(spent_at__date=d).aggregate(s=Sum("amount"))["s"] or 0
        profit = revenue - expense

        # Top sold items (qty)
        top_items = (
            OrderItem.objects.filter(created_at__date=d)
            .values("item_name_snapshot")
            .annotate(qty=Sum("qty"), amount=Sum("line_total"))
            .order_by("-qty")[:10]
        )

        return Response({
            "date": str(d),
            "revenue": revenue,
            "expense": expense,
            "profit": profit,
            "top_items": list(top_items),
        })


class RangeReportView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        df = parse_date(request.query_params.get("date_from", ""))
        dt = parse_date(request.query_params.get("date_to", ""))

        if not df or not dt:
            return Response({"detail": "date_from va date_to majburiy."}, status=400)

        revenue = Payment.objects.filter(is_debt=False, paid_at__date__gte=df, paid_at__date__lte=dt).aggregate(s=Sum("amount"))["s"] or 0
        expense = Expense.objects.filter(spent_at__date__gte=df, spent_at__date__lte=dt).aggregate(s=Sum("amount"))["s"] or 0
        profit = revenue - expense

        top_items = (
            OrderItem.objects.filter(created_at__date__gte=df, created_at__date__lte=dt)
            .values("item_name_snapshot")
            .annotate(qty=Sum("qty"), amount=Sum("line_total"))
            .order_by("-qty")[:20]
        )

        return Response({
            "date_from": str(df),
            "date_to": str(dt),
            "revenue": revenue,
            "expense": expense,
            "profit": profit,
            "top_items": list(top_items),
        })
