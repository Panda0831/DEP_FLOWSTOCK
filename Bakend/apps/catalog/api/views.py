from django.db.models import ProtectedError
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminRole
from apps.inventory.api.serializers import MouvementSerializer, StockSerializer
from apps.inventory.models import Mouvement
from apps.inventory.services import stock_actuel

from ..models import Categorie, Fournisseur, Produit
from .serializers import CategorieSerializer, FournisseurSerializer, ProduitSerializer


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Cette ressource est utilisée et ne peut pas être supprimée."
    default_code = "conflict"


class ProtectedDeleteMixin:
    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ConflictError()


class CategorieViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    lookup_field = "public_id"

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return (IsAdminRole(),)
        return (IsAuthenticated(),)


class FournisseurViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer
    lookup_field = "public_id"

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return (IsAdminRole(),)
        return (IsAuthenticated(),)


class ProduitViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Produit.objects.all()
    serializer_class = ProduitSerializer
    lookup_field = "public_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search")
        category = self.request.query_params.get("category")
        supplier = self.request.query_params.get("supplier")
        active = self.request.query_params.get("active")
        if search:
            queryset = queryset.filter(nomProduit__icontains=search)
        if category:
            queryset = queryset.filter(idCategorie__public_id=category)
        if supplier:
            queryset = queryset.filter(idFournisseur__public_id=supplier)
        if active is not None:
            if active.lower() not in ("true", "false"):
                raise ValidationError({"active": "Utilisez true ou false."})
            queryset = queryset.filter(isActif=active.lower() == "true")
        ordering = self.request.query_params.get("ordering")
        allowed_ordering = {
            "nomProduit",
            "-nomProduit",
            "prixVente",
            "-prixVente",
            "seuilAlerte",
            "-seuilAlerte",
        }
        if ordering:
            if ordering not in allowed_ordering:
                raise ValidationError({"ordering": "Critère de tri non autorisé."})
            queryset = queryset.order_by(ordering)
        return queryset

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
            "deactivate",
        ):
            return (IsAdminRole(),)
        return (IsAuthenticated(),)

    @action(detail=False, methods=("get",), url_path="low-stock")
    @extend_schema(responses=ProduitSerializer(many=True))
    def low_stock(self, request):
        produits = [
            produit
            for produit in self.filter_queryset(self.get_queryset())
            if produit.isActif and stock_actuel(produit) <= produit.seuilAlerte
        ]
        page = self.paginate_queryset(produits)
        serializer = self.get_serializer(page or produits, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=("get",))
    @extend_schema(responses=StockSerializer)
    def stock(self, request, public_id=None):
        produit = self.get_object()
        return Response(
            {
                "public_id": str(produit.public_id),
                "nomProduit": produit.nomProduit,
                "stock": stock_actuel(produit),
                "seuilAlerte": produit.seuilAlerte,
            }
        )

    @action(detail=True, methods=("get",))
    @extend_schema(responses=MouvementSerializer(many=True))
    def movements(self, request, public_id=None):
        produit = self.get_object()
        mouvements = Mouvement.objects.filter(idProduit=produit).select_related(
            "idProduit", "idUser"
        )
        page = self.paginate_queryset(mouvements)
        serializer = MouvementSerializer(page or mouvements, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=("post",))
    def deactivate(self, request, public_id=None):
        produit = self.get_object()
        produit.isActif = False
        produit.save(update_fields=("isActif",))
        return Response(self.get_serializer(produit).data)

    def destroy(self, request, *args, **kwargs):
        produit = self.get_object()
        if produit.mouvements.exists() or produit.lignes_commande.exists():
            return Response(
                {"detail": "Un produit historique ne peut qu'être désactivé."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)
