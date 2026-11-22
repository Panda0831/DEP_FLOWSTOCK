from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.accounts.permissions import IsAdminRole
from apps.catalog.models import Produit

from ..models import Mouvement
from ..services import enregistrer_mouvement, stock_actuel
from .serializers import (
    MouvementCreationSerializer,
    MouvementSerializer,
    StockSerializer,
)


class MovementViewSet(ReadOnlyModelViewSet):
    queryset = Mouvement.objects.select_related("idProduit", "idUser")
    serializer_class = MouvementSerializer
    permission_classes = (IsAuthenticated,)


class MouvementAPIView(APIView):
    permission_classes = (IsAdminRole,)
    type_mouvement = None

    @extend_schema(
        request=MouvementCreationSerializer,
        responses={201: MouvementSerializer},
    )
    def post(self, request):
        serializer = MouvementCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mouvement = enregistrer_mouvement(
            public_id=serializer.validated_data["product"],
            type_mouvement=self.type_mouvement,
            quantite=serializer.validated_data["quantity"],
            user=request.user,
            motif=serializer.validated_data.get("motif", ""),
        )
        return Response(MouvementSerializer(mouvement).data, status=201)


class EntreeAPIView(MouvementAPIView):
    type_mouvement = "entree"


class PerteAPIView(MouvementAPIView):
    type_mouvement = "perte"


class StockAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=StockSerializer(many=True))
    def get(self, request):
        data = [
            {
                "public_id": str(produit.public_id),
                "nomProduit": produit.nomProduit,
                "stock": stock_actuel(produit),
                "seuilAlerte": produit.seuilAlerte,
            }
            for produit in Produit.objects.filter(isActif=True)
        ]
        return Response(data)


class AlertsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=StockSerializer(many=True))
    def get(self, request):
        data = [
            {
                "public_id": str(produit.public_id),
                "nomProduit": produit.nomProduit,
                "stock": stock_actuel(produit),
                "seuilAlerte": produit.seuilAlerte,
            }
            for produit in Produit.objects.filter(isActif=True)
            if stock_actuel(produit) <= produit.seuilAlerte
        ]
        return Response(data)
