from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminRole

from ..models import Achat, ReceptionAchat
from ..services import annuler_achat, creer_achat, modifier_achat, recevoir_achat, retourner_achat
from .serializers import (
    AchatCreationSerializer,
    AchatSerializer,
    AchatUpdateSerializer,
    ReceptionAchatSerializer,
    ReceptionCreationSerializer,
    RetourAchatCreationSerializer,
)


class AchatViewSet(viewsets.ModelViewSet):
    queryset = (
        Achat.objects.select_related("idFournisseur", "idUser")
        .prefetch_related(
            "lignes__idProduit",
            "receptions__lignes__idLigneAchat__idProduit",
            "paiements",
            "historique__idUser",
        )
        .all()
    )
    serializer_class = AchatSerializer
    permission_classes = (IsAdminRole,)
    lookup_field = "public_id"
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_serializer_class(self):
        if self.action == "create":
            return AchatCreationSerializer
        if self.action == "partial_update":
            return AchatUpdateSerializer
        return AchatSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        achat = creer_achat(
            fournisseur_id=data["supplier"],
            items=data["items"],
            user=request.user,
            date_commande=data["dateCommande"],
            lieu=data.get("lieuAchat", ""),
            mode_obtention=data["modeObtention"],
        )
        return Response(
            AchatSerializer(achat, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        achat = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        achat = modifier_achat(
            achat=achat,
            fournisseur_id=data.get("supplier"),
            items=data.get("items"),
            date_commande=data.get("dateCommande"),
            lieu=data.get("lieuAchat"),
            mode_obtention=data.get("modeObtention"),
            user=request.user,
        )
        return Response(AchatSerializer(achat, context={"request": request}).data)

    @action(detail=True, methods=("post",), url_path="receive")
    def receive(self, request, public_id=None):
        achat = self.get_object()
        serializer = ReceptionCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        reception = recevoir_achat(
            achat=achat,
            items=data["items"],
            user=request.user,
            date=data["date"],
            lieu=data.get("lieu", ""),
            commentaire=data.get("commentaire", ""),
        )
        return Response(
            ReceptionAchatSerializer(reception, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=("post",), url_path="cancel")
    def cancel(self, request, public_id=None):
        achat = annuler_achat(achat=self.get_object(), user=request.user)
        return Response(AchatSerializer(achat, context={"request": request}).data)

    @action(detail=True, methods=("post",), url_path="return-to-supplier")
    def return_to_supplier(self, request, public_id=None):
        serializer = RetourAchatCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        achat = retourner_achat(
            achat=self.get_object(),
            items=data["items"],
            user=request.user,
            date=data["date"],
            motif=data.get("motif", ""),
        )
        return Response(AchatSerializer(achat, context={"request": request}).data, status=201)


class ReceptionAchatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReceptionAchat.objects.select_related("idAchat", "idUser").prefetch_related(
        "lignes__idLigneAchat__idProduit"
    )
    serializer_class = ReceptionAchatSerializer
    permission_classes = (IsAdminRole,)
    lookup_field = "public_id"
