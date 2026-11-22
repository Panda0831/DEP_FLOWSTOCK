from io import BytesIO

from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, has_role
from apps.accounts.services import security_event
from apps.sales.models import Commande

from ..models import Depense, Paiement
from ..services import (
    calculer_resume,
    enregistrer_paiement,
    produits_en_alerte,
    rapport_commandes,
    rapport_mensuel,
    rapport_produits,
)
from .serializers import (
    AlerteStockSerializer,
    CommandeEnAttenteSerializer,
    DepenseSerializer,
    PaiementCreationSerializer,
    PaiementSerializer,
    RapportCommandeSerializer,
    RapportMensuelSerializer,
    RapportProduitSerializer,
    ResumeFinancierSerializer,
    TableauDeBordSerializer,
)

DATE_PARAMETERS = [
    OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
    OpenApiParameter("end_date", OpenApiTypes.DATE, OpenApiParameter.QUERY),
]
DASHBOARD_DATE_PARAMETERS = [
    OpenApiParameter("start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
    OpenApiParameter("end_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False),
]


class DepenseViewSet(viewsets.ModelViewSet):
    queryset = Depense.objects.all()
    serializer_class = DepenseSerializer
    permission_classes = (IsAdminRole,)
    lookup_field = "public_id"


def periode(request, *, required=True):
    debut_raw = request.query_params.get("start_date")
    fin_raw = request.query_params.get("end_date")
    if not required and not debut_raw and not fin_raw:
        aujourd_hui = timezone.localdate()
        return aujourd_hui.replace(day=1), aujourd_hui
    debut = parse_date(debut_raw or "")
    fin = parse_date(fin_raw or "")
    if not debut or not fin or fin < debut or (fin - debut).days > 365:
        raise ValidationError(
            {
                "detail": (
                    "Période invalide : fournissez start_date et end_date, "
                    "dans l'ordre, sur une durée maximale d'un an."
                )
            }
        )
    return debut, fin


class ReportSummaryAPIView(APIView):
    permission_classes = (IsAdminRole,)

    @extend_schema(parameters=DATE_PARAMETERS, responses=ResumeFinancierSerializer)
    def get(self, request):
        debut, fin = periode(request)
        return Response(calculer_resume(debut, fin))


class ReportProductsAPIView(APIView):
    permission_classes = (IsAdminRole,)

    @extend_schema(
        parameters=DATE_PARAMETERS,
        responses=RapportProduitSerializer(many=True),
    )
    def get(self, request):
        debut, fin = periode(request)
        return Response(rapport_produits(debut, fin))


class ReportOrdersAPIView(APIView):
    permission_classes = (IsAdminRole,)

    @extend_schema(
        parameters=DATE_PARAMETERS,
        responses=RapportCommandeSerializer(many=True),
    )
    def get(self, request):
        debut, fin = periode(request)
        return Response(rapport_commandes(debut, fin))


class ReportMonthlyAPIView(APIView):
    permission_classes = (IsAdminRole,)

    @extend_schema(
        parameters=DATE_PARAMETERS,
        responses=RapportMensuelSerializer(many=True),
    )
    def get(self, request):
        debut, fin = periode(request)
        return Response(rapport_mensuel(debut, fin))


class DashboardAPIView(APIView):
    permission_classes = (IsAdminRole,)

    @extend_schema(
        parameters=DASHBOARD_DATE_PARAMETERS,
        responses=TableauDeBordSerializer,
    )
    def get(self, request):
        debut, fin = periode(request, required=False)
        return Response(
            {
                "resume_financier": calculer_resume(debut, fin),
                "alertes_stock": produits_en_alerte(),
                "commandes_en_attente": Commande.objects.filter(
                    statut=Commande.Statut.EN_ATTENTE
                ).count(),
            }
        )


class StockAlertsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=AlerteStockSerializer(many=True))
    def get(self, request):
        return Response(produits_en_alerte())


class PendingOrdersAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(responses=CommandeEnAttenteSerializer(many=True))
    def get(self, request):
        commandes = Commande.objects.filter(statut=Commande.Statut.EN_ATTENTE)
        if not has_role(request.user, "ADMIN"):
            commandes = commandes.filter(idUser=request.user)
        return Response(
            [
                {
                    "public_id": str(commande.public_id),
                    "date": commande.date,
                    "client": commande.idClient.nomClient,
                }
                for commande in commandes.select_related("idClient").order_by("date")
            ]
        )


def excel_safe(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


class ExcelExportAPIView(APIView):
    permission_classes = (IsAdminRole,)

    @extend_schema(
        parameters=DATE_PARAMETERS,
        responses={(200): OpenApiTypes.BINARY},
    )
    def get(self, request):
        debut, fin = periode(request)
        from openpyxl import Workbook

        workbook = Workbook()
        resume_sheet = workbook.active
        resume_sheet.title = "Résumé"
        resume = calculer_resume(debut, fin)
        resume_sheet.append(["Période", str(debut), str(fin)])
        resume_sheet.append(["Commandes livrées", resume["commandes_livrees"]])
        for label, key in (
            ("Chiffre d'affaires", "chiffre_affaires"),
            ("Bénéfice brut", "benefice_brut"),
            ("Dépenses", "depenses"),
            ("Bénéfice net", "benefice_net"),
        ):
            resume_sheet.append([label, resume[key]])

        produits_sheet = workbook.create_sheet("Produits")
        produits_sheet.append(["Produit", "Quantité vendue", "Chiffre d'affaires", "Bénéfice brut"])
        for row in rapport_produits(debut, fin):
            produits_sheet.append(
                [
                    excel_safe(row["idProduit__nomProduit"]),
                    row["quantite_vendue"],
                    row["chiffre_affaires"],
                    row["benefice_brut"],
                ]
            )

        stock_sheet = workbook.create_sheet("Stock")
        stock_sheet.append(["Produit", "Stock actuel", "Seuil d'alerte", "Sous le seuil"])
        from apps.catalog.models import Produit
        from apps.inventory.services import stock_actuel

        for produit in Produit.objects.filter(isActif=True).order_by("nomProduit"):
            stock = stock_actuel(produit)
            stock_sheet.append(
                [
                    excel_safe(produit.nomProduit),
                    stock,
                    produit.seuilAlerte,
                    stock <= produit.seuilAlerte,
                ]
            )

        depenses_sheet = workbook.create_sheet("Dépenses")
        depenses_sheet.append(["Date", "Libellé", "Montant"])
        for depense in Depense.objects.filter(date__range=(debut, fin)).order_by(
            "date", "idDepense"
        ):
            depenses_sheet.append([depense.date, excel_safe(depense.libelle), depense.montant])

        buffer = BytesIO()
        workbook.save(buffer)
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="rapport_flowstock.xlsx"'
        response["Cache-Control"] = "no-store"
        security_event(
            "report_exported",
            user=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
            start_date=debut,
            end_date=fin,
        )
        return response


class PaiementsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        paiements = Paiement.objects.select_related("idCommande", "idAchat").all()
        if not has_role(request.user, "ADMIN"):
            paiements = paiements.filter(idCommande__idUser=request.user)
        operation = request.query_params.get("operation")
        public_id = request.query_params.get("public_id")
        if operation not in (None, "order", "purchase"):
            raise ValidationError({"operation": "Type d'opération invalide."})
        if operation == "order":
            paiements = paiements.filter(idCommande__public_id=public_id) if public_id else paiements.filter(idCommande__isnull=False)
        elif operation == "purchase":
            paiements = paiements.filter(idAchat__public_id=public_id) if public_id else paiements.filter(idAchat__isnull=False)
        elif public_id:
            paiements = paiements.filter(
                Q(idCommande__public_id=public_id) | Q(idAchat__public_id=public_id)
            )
        return Response(PaiementSerializer(paiements, many=True).data)

    def post(self, request):
        serializer = PaiementCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data["operation"] == "purchase":
            if not has_role(request.user, "ADMIN"):
                raise PermissionDenied("Seul un administrateur peut enregistrer un paiement fournisseur.")
        else:
            commande = Commande.objects.filter(public_id=data["public_id"]).first()
            if commande is None:
                raise ValidationError({"order": "Commande introuvable."})
            if not has_role(request.user, "ADMIN") and commande.idUser_id != request.user.pk:
                raise PermissionDenied("Vous ne pouvez enregistrer un paiement que sur vos commandes.")
        paiement = enregistrer_paiement(
            type_operation=data["operation"],
            public_id=data["public_id"],
            montant=data["montant"],
            date=data["date"],
            mode=data["mode"],
            reference=data.get("reference", ""),
            commentaire=data.get("commentaire", ""),
            user=request.user,
            type_paiement=data["typePaiement"],
        )
        return Response(PaiementSerializer(paiement).data, status=201)
