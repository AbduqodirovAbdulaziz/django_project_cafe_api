from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from menu.views import CategoryViewSet, MenuItemViewSet
from tables.views import TableViewSet
from orders.views import OrderViewSet
from payments.views import PaymentViewSet
from expenses.views import ExpenseCategoryViewSet, ExpenseViewSet
from reports.views import DailyReportView, RangeReportView, WaiterStatsView

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"menu-items", MenuItemViewSet, basename="menu-item")
router.register(r"tables", TableViewSet, basename="table")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"expense-categories", ExpenseCategoryViewSet, basename="expense-category")
router.register(r"expenses", ExpenseViewSet, basename="expense")

urlpatterns = [
    path("", include(router.urls)),
    # OpenAPI schema and interactive docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("reports/daily/", DailyReportView.as_view(), name="report-daily"),
    path("reports/range/", RangeReportView.as_view(), name="report-range"),
    path("reports/waiter-stats/", WaiterStatsView.as_view(), name="report-waiter-stats"),
]
