from rest_framework.routers import DefaultRouter

from .views import ClientViewSet, CommandeViewSet, LivraisonViewSet

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="client")
router.register("orders", CommandeViewSet, basename="commande")
router.register("deliveries", LivraisonViewSet, basename="livraison")
urlpatterns = router.urls
