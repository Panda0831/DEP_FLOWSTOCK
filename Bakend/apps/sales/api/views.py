from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminRole, has_role

from ..models import Client, Commande, Livraison
from ..services import (
    annuler_commande,
    confirmer_commande,
    creer_commande,
    modifier_commande,
    modifier_statut_livraison,
)
from .serializers import (
    ClientSerializer,
    CommandeCreationSerializer,
    CommandeSerializer,
    CommandeUpdateSerializer,
    LivraisonSerializer,
)


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Cette ressource ne peut pas être supprimée."
    default_code = "conflict"


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "public_id"

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(nomClient__icontains=search)
        return queryset

    def get_permissions(self):
        if self.action == "destroy":
            return (IsAdminRole(),)
        return (IsAuthenticated(),)

    def perform_destroy(self, instance):
        if instance.commandes.exists():
            raise ConflictError("Un client ayant des commandes ne peut pas être supprimé.")
        try:
            instance.delete()
        except ProtectedError:
            raise ConflictError()


class CommandeViewSet(viewsets.ModelViewSet):
    queryset = Commande.objects.select_related("idClient", "idUser").prefetch_related(
        "lignes__idProduit", "paiements"
    )
    serializer_class = CommandeSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "public_id"
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_serializer_class(self):
        if self.action == "create":
            return CommandeCreationSerializer
        if self.action == "partial_update":
            return CommandeUpdateSerializer
        return CommandeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if not has_role(self.request.user, "ADMIN"):
            queryset = queryset.filter(idUser=self.request.user)
        return queryset

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            client = Client.objects.get(public_id=serializer.validated_data["client"])
        except Client.DoesNotExist:
            raise ValidationError({"client": "Client introuvable."})
        commande = creer_commande(
            client=client,
            items=serializer.validated_data["items"],
            user=request.user,
            remise=serializer.validated_data["remise"],
            frais_livraison=serializer.validated_data["fraisLivraison"],
        )
        return Response(CommandeSerializer(commande, context={"request": request}).data, status=201)

    def partial_update(self, request, *args, **kwargs):
        commande = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        client = None
        if "client" in serializer.validated_data:
            try:
                client = Client.objects.get(public_id=serializer.validated_data["client"])
            except Client.DoesNotExist:
                raise ValidationError({"client": "Client introuvable."})
        commande = modifier_commande(
            commande=commande,
            client=client,
            items=serializer.validated_data.get("items"),
            remise=serializer.validated_data.get("remise"),
            frais_livraison=serializer.validated_data.get("fraisLivraison"),
        )
        return Response(CommandeSerializer(commande, context={"request": request}).data)

    @action(detail=True, methods=("post",), permission_classes=(IsAuthenticated,))
    def confirm(self, request, public_id=None):
        commande = confirmer_commande(commande=self.get_object(), user=request.user)
        return Response(CommandeSerializer(commande, context={"request": request}).data)

    @action(detail=True, methods=("post",), permission_classes=(IsAuthenticated,))
    def cancel(self, request, public_id=None):
        commande = annuler_commande(commande=self.get_object(), user=request.user)
        return Response(CommandeSerializer(commande, context={"request": request}).data)


class LivraisonViewSet(viewsets.ModelViewSet):
    queryset = Livraison.objects.select_related("idCommande")
    serializer_class = LivraisonSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "public_id"
    http_method_names = ("get", "post", "patch", "head", "options")

    def get_queryset(self):
        queryset = super().get_queryset()
        if not has_role(self.request.user, "ADMIN"):
            queryset = queryset.filter(idCommande__idUser=self.request.user)
        return queryset

    def perform_create(self, serializer):
        commande = Commande.objects.filter(
            public_id=serializer.validated_data.get("commande")
        ).first()
        if commande is None:
            raise ValidationError({"commande": "Commande introuvable."})
        if not has_role(self.request.user, "ADMIN") and commande.idUser_id != self.request.user.pk:
            raise PermissionDenied("Vous ne pouvez gérer que vos propres livraisons.")
        serializer.save()

    @action(detail=True, methods=("post",), url_path="mark-delivered")
    def mark_delivered(self, request, public_id=None):
        livraison = modifier_statut_livraison(
            livraison=self.get_object(), action="delivered", user=request.user
        )
        return Response(self.get_serializer(livraison).data)

    @action(detail=True, methods=("post",), url_path="mark-failed")
    def mark_failed(self, request, public_id=None):
        livraison = modifier_statut_livraison(
            livraison=self.get_object(), action="failed", user=request.user
        )
        return Response(self.get_serializer(livraison).data)

    @action(detail=True, methods=("post",), url_path="mark-preparing")
    def mark_preparing(self, request, public_id=None):
        livraison = modifier_statut_livraison(
            livraison=self.get_object(), action="preparing", user=request.user
        )
        return Response(self.get_serializer(livraison).data)

    @action(detail=True, methods=("post",), url_path="mark-shipped")
    def mark_shipped(self, request, public_id=None):
        livraison = modifier_statut_livraison(
            livraison=self.get_object(), action="shipped", user=request.user
        )
        return Response(self.get_serializer(livraison).data)

    @action(detail=True, methods=("post",), url_path="retry")
    def retry(self, request, public_id=None):
        livraison = modifier_statut_livraison(
            livraison=self.get_object(), action="retry", user=request.user
        )
        return Response(self.get_serializer(livraison).data)

    @action(detail=True, methods=("post",), url_path="mark-returned")
    def mark_returned(self, request, public_id=None):
        livraison = modifier_statut_livraison(
            livraison=self.get_object(), action="returned", user=request.user
        )
        return Response(self.get_serializer(livraison).data)
