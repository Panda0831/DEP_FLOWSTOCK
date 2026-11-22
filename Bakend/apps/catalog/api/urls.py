from rest_framework.routers import DefaultRouter

from .views import CategorieViewSet, FournisseurViewSet, ProduitViewSet

router = DefaultRouter()
router.register("categories", CategorieViewSet, basename="categorie")
router.register("suppliers", FournisseurViewSet, basename="fournisseur")
router.register("products", ProduitViewSet, basename="produit")
urlpatterns = router.urls
