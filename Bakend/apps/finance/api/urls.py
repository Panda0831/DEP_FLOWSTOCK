from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardAPIView,
    DepenseViewSet,
    ExcelExportAPIView,
    PaiementsAPIView,
    PendingOrdersAPIView,
    ReportMonthlyAPIView,
    ReportOrdersAPIView,
    ReportProductsAPIView,
    ReportSummaryAPIView,
    StockAlertsAPIView,
)

router = DefaultRouter()
router.register("expenses", DepenseViewSet, basename="depense")
urlpatterns = router.urls + [
    path("dashboard/summary/", DashboardAPIView.as_view(), name="dashboard-summary"),
    path("payments/", PaiementsAPIView.as_view(), name="payments"),
    path("dashboard/stock-alerts/", StockAlertsAPIView.as_view(), name="dashboard-stock-alerts"),
    path(
        "dashboard/pending-orders/", PendingOrdersAPIView.as_view(), name="dashboard-pending-orders"
    ),
    path("reports/summary/", ReportSummaryAPIView.as_view(), name="reports-summary"),
    path("reports/products/", ReportProductsAPIView.as_view(), name="reports-products"),
    path("reports/orders/", ReportOrdersAPIView.as_view(), name="reports-orders"),
    path("reports/monthly/", ReportMonthlyAPIView.as_view(), name="reports-monthly"),
    path("exports/excel/", ExcelExportAPIView.as_view(), name="exports-excel"),
]
