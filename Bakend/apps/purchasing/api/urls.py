from rest_framework.routers import DefaultRouter

from .views import AchatViewSet, ReceptionAchatViewSet

router = DefaultRouter()
router.register("purchases", AchatViewSet, basename="achat")
router.register("purchase-receptions", ReceptionAchatViewSet, basename="reception-achat")

urlpatterns = router.urls
