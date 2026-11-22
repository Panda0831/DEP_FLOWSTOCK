from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AlertsAPIView, EntreeAPIView, MovementViewSet, PerteAPIView, StockAPIView

router = DefaultRouter()
router.register("movements", MovementViewSet, basename="mouvement")
urlpatterns = [
    path("stock/", StockAPIView.as_view(), name="stock-list"),
    path("stock/alerts/", AlertsAPIView.as_view(), name="stock-alerts"),
    path("movements/entries/", EntreeAPIView.as_view(), name="mouvement-entree"),
    path("movements/losses/", PerteAPIView.as_view(), name="mouvement-perte"),
] + router.urls
