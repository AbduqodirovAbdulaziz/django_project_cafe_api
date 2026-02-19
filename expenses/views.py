from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date

from accounts.permissions import IsManager
from .models import ExpenseCategory, Expense
from .serializers import ExpenseCategorySerializer, ExpenseSerializer


class ExpenseCategoryViewSet(ModelViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated, IsManager]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]


class ExpenseViewSet(ModelViewSet):
    queryset = Expense.objects.select_related("category", "created_by").all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated, IsManager]
    ordering_fields = ["spent_at", "amount", "id"]

    def get_queryset(self):
        qs = super().get_queryset()
        qp = self.request.query_params
        date_from = qp.get("date_from")
        date_to = qp.get("date_to")
        category = qp.get("category")

        if category:
            qs = qs.filter(category_id=category)
        if date_from:
            d1 = parse_date(date_from)
            if d1:
                qs = qs.filter(spent_at__date__gte=d1)
        if date_to:
            d2 = parse_date(date_to)
            if d2:
                qs = qs.filter(spent_at__date__lte=d2)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
