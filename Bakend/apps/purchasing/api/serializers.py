from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from apps.finance.api.serializers import PaiementSerializer
from apps.finance.services import (
    montant_paye,
    montant_remboursable,
    montant_restant,
    montant_retourne,
    montant_total_net,
)
from apps.inventory.models import Mouvement

from ..models import Achat, HistoriqueAchat, LigneAchat, LigneReceptionAchat, ReceptionAchat


class HistoriqueAchatSerializer(serializers.ModelSerializer):
    utilisateur = serializers.CharField(source="idUser.email", read_only=True)

    class Meta:
        model = HistoriqueAchat
        fields = ("evenement", "date", "utilisateur", "referenceOperation", "details")


class LigneAchatSerializer(serializers.ModelSerializer):
    product = serializers.UUIDField(source="idProduit.public_id", read_only=True)
    nomProduit = serializers.CharField(source="idProduit.nomProduit", read_only=True)
    quantite_recue = serializers.SerializerMethodField()
    quantite_retournee = serializers.SerializerMethodField()

    class Meta:
        model = LigneAchat
        fields = (
            "product",
            "nomProduit",
            "quantite",
            "quantite_recue",
            "quantite_retournee",
            "prixUnitaire",
        )

    def get_quantite_recue(self, obj):
        return (
            LigneReceptionAchat.objects.filter(idLigneAchat=obj).aggregate(total=Sum("quantite"))[
                "total"
            ]
            or 0
        )

    def get_quantite_retournee(self, obj):
        return (
            Mouvement.objects.filter(
                idProduit=obj.idProduit,
                typeMouvement=Mouvement.TypeMouvement.RETOUR_FOURNISSEUR,
                referenceOperation=obj.idAchat.reference,
            ).aggregate(total=Sum("quantite"))["total"]
            or 0
        )


class ReceptionAchatSerializer(serializers.ModelSerializer):
    achat = serializers.UUIDField(source="idAchat.public_id", read_only=True)
    lignes = serializers.SerializerMethodField()

    class Meta:
        model = ReceptionAchat
        fields = (
            "public_id",
            "reference",
            "achat",
            "date",
            "lieu",
            "commentaire",
            "lignes",
        )

    def get_lignes(self, obj):
        return [
            {
                "product": str(ligne.idLigneAchat.idProduit.public_id),
                "nomProduit": ligne.idLigneAchat.idProduit.nomProduit,
                "quantite": ligne.quantite,
            }
            for ligne in obj.lignes.select_related("idLigneAchat__idProduit")
        ]


class AchatSerializer(serializers.ModelSerializer):
    supplier = serializers.UUIDField(source="idFournisseur.public_id", read_only=True)
    nomFournisseur = serializers.CharField(source="idFournisseur.nomFournisseur", read_only=True)
    lignes = LigneAchatSerializer(many=True, read_only=True)
    receptions = ReceptionAchatSerializer(many=True, read_only=True)
    paiements = PaiementSerializer(many=True, read_only=True)
    historique = HistoriqueAchatSerializer(many=True, read_only=True)
    montant_total = serializers.SerializerMethodField()
    montant_retourne = serializers.SerializerMethodField()
    montant_net = serializers.SerializerMethodField()
    montant_paye = serializers.SerializerMethodField()
    solde_restant = serializers.SerializerMethodField()
    montant_remboursable = serializers.SerializerMethodField()
    statut_paiement = serializers.SerializerMethodField()

    class Meta:
        model = Achat
        fields = (
            "public_id",
            "reference",
            "supplier",
            "nomFournisseur",
            "dateCommande",
            "lieuAchat",
            "modeObtention",
            "statut",
            "lignes",
            "receptions",
            "paiements",
            "historique",
            "montant_total",
            "montant_retourne",
            "montant_net",
            "montant_paye",
            "solde_restant",
            "montant_remboursable",
            "statut_paiement",
        )

    def get_montant_total(self, obj):
        return obj.montant_total

    def get_montant_retourne(self, obj):
        return montant_retourne(obj)

    def get_montant_net(self, obj):
        return montant_total_net(obj)

    def get_montant_paye(self, obj):
        return montant_paye(obj)

    def get_solde_restant(self, obj):
        return montant_restant(obj)

    def get_statut_paiement(self, obj):
        paye = montant_paye(obj)
        if montant_remboursable(obj) > 0:
            return "remboursement_attendu"
        if montant_restant(obj) == 0:
            return "paye"
        if paye == 0:
            return "non_paye"
        return "partiellement_paye"

    def get_montant_remboursable(self, obj):
        return montant_remboursable(obj)


class AchatCreationSerializer(serializers.Serializer):
    supplier = serializers.UUIDField()
    dateCommande = serializers.DateField(required=False, default=timezone.localdate)
    lieuAchat = serializers.CharField(max_length=180, required=False, allow_blank=True)
    modeObtention = serializers.ChoiceField(choices=Achat.Obtention.choices, default="commande")
    items = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate_items(self, items):
        cleaned = []
        products = set()
        product_field = serializers.UUIDField()
        quantity_field = serializers.IntegerField(min_value=1)
        price_field = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal(0))
        for item in items:
            try:
                product = product_field.run_validation(item["product"])
                quantity = quantity_field.run_validation(item["quantity"])
                unit_price = price_field.run_validation(item["unit_price"])
            except (KeyError, TypeError, ValueError, serializers.ValidationError):
                raise serializers.ValidationError(
                    "Chaque ligne doit contenir product, quantity et unit_price."
                )
            if product in products:
                raise serializers.ValidationError("Un produit ne peut apparaître qu'une fois.")
            products.add(product)
            cleaned.append({"product": product, "quantity": quantity, "unit_price": unit_price})
        return cleaned


class AchatUpdateSerializer(AchatCreationSerializer):
    supplier = serializers.UUIDField(required=False)
    dateCommande = serializers.DateField(required=False)
    lieuAchat = serializers.CharField(max_length=180, required=False, allow_blank=True)
    modeObtention = serializers.ChoiceField(choices=Achat.Obtention.choices, required=False)
    items = serializers.ListField(child=serializers.DictField(), required=False, allow_empty=False)


class ReceptionCreationSerializer(serializers.Serializer):
    date = serializers.DateField(required=False, default=timezone.localdate)
    lieu = serializers.CharField(max_length=180, required=False, allow_blank=True)
    commentaire = serializers.CharField(max_length=255, required=False, allow_blank=True)
    items = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate_items(self, items):
        cleaned = []
        products = set()
        product_field = serializers.UUIDField()
        quantity_field = serializers.IntegerField(min_value=1)
        for item in items:
            try:
                product = product_field.run_validation(item["product"])
                quantity = quantity_field.run_validation(item["quantity"])
            except (KeyError, TypeError, ValueError, serializers.ValidationError):
                raise serializers.ValidationError("Chaque ligne doit contenir product et quantity.")
            if product in products:
                raise serializers.ValidationError("Un produit ne peut apparaître qu'une fois.")
            products.add(product)
            cleaned.append({"product": product, "quantity": quantity})
        return cleaned


class RetourAchatCreationSerializer(serializers.Serializer):
    date = serializers.DateField(required=False, default=timezone.localdate)
    motif = serializers.CharField(max_length=255, required=False, allow_blank=True)
    items = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate_items(self, items):
        cleaned = []
        products = set()
        product_field = serializers.UUIDField()
        quantity_field = serializers.IntegerField(min_value=1)
        for item in items:
            try:
                product = product_field.run_validation(item["product"])
                quantity = quantity_field.run_validation(item["quantity"])
            except (KeyError, TypeError, ValueError, serializers.ValidationError):
                raise serializers.ValidationError("Chaque ligne doit contenir product et quantity.")
            if product in products:
                raise serializers.ValidationError("Un produit ne peut apparaître qu'une fois.")
            products.add(product)
            cleaned.append({"product": product, "quantity": quantity})
        return cleaned
