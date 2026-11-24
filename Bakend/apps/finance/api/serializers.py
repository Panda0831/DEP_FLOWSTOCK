from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from ..models import Depense, Paiement


class ResumeFinancierSerializer(serializers.Serializer):
    chiffre_affaires = serializers.DecimalField(max_digits=18, decimal_places=2)
    ventes_produits = serializers.DecimalField(max_digits=18, decimal_places=2)
    remises = serializers.DecimalField(max_digits=18, decimal_places=2)
    frais_livraison_factures = serializers.DecimalField(max_digits=18, decimal_places=2)
    cout_produits = serializers.DecimalField(max_digits=18, decimal_places=2)
    cout_livraisons = serializers.DecimalField(max_digits=18, decimal_places=2)
    benefice_brut = serializers.DecimalField(max_digits=18, decimal_places=2)
    depenses = serializers.DecimalField(max_digits=18, decimal_places=2)
    benefice_net = serializers.DecimalField(max_digits=18, decimal_places=2)
    commandes_livrees = serializers.IntegerField()


class RapportProduitSerializer(serializers.Serializer):
    idProduit__public_id = serializers.UUIDField()
    idProduit__nomProduit = serializers.CharField()
    quantite_vendue = serializers.IntegerField()
    chiffre_affaires = serializers.DecimalField(max_digits=18, decimal_places=2)
    benefice_brut = serializers.DecimalField(max_digits=18, decimal_places=2)


class RapportCommandeSerializer(serializers.Serializer):
    public_id = serializers.UUIDField()
    client = serializers.CharField()
    date_livraison = serializers.DateField()
    chiffre_affaires = serializers.DecimalField(max_digits=18, decimal_places=2)
    benefice = serializers.DecimalField(max_digits=18, decimal_places=2)


class RapportMensuelSerializer(serializers.Serializer):
    mois = serializers.DateField()
    benefice_brut = serializers.DecimalField(max_digits=18, decimal_places=2)
    depenses = serializers.DecimalField(max_digits=18, decimal_places=2)
    benefice_net = serializers.DecimalField(max_digits=18, decimal_places=2)


class AlerteStockSerializer(serializers.Serializer):
    public_id = serializers.UUIDField()
    nomProduit = serializers.CharField()
    stock = serializers.IntegerField()
    seuilAlerte = serializers.IntegerField()


class CommandeEnAttenteSerializer(serializers.Serializer):
    public_id = serializers.UUIDField()
    date = serializers.DateField()
    client = serializers.CharField()


class TableauDeBordSerializer(serializers.Serializer):
    resume_financier = ResumeFinancierSerializer()
    alertes_stock = AlerteStockSerializer(many=True)
    commandes_en_attente = serializers.IntegerField()


class DepenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depense
        fields = ("public_id", "date", "libelle", "montant")
        read_only_fields = ("public_id",)

    def validate_montant(self, value):
        if value < 0:
            raise serializers.ValidationError("Le montant doit être positif ou nul.")
        return value


class PaiementSerializer(serializers.ModelSerializer):
    commande = serializers.UUIDField(source="idCommande.public_id", read_only=True, allow_null=True)
    reference_commande = serializers.CharField(
        source="idCommande.reference", read_only=True, allow_null=True
    )
    achat = serializers.UUIDField(source="idAchat.public_id", read_only=True, allow_null=True)
    reference_achat = serializers.CharField(
        source="idAchat.reference", read_only=True, allow_null=True
    )

    class Meta:
        model = Paiement
        fields = (
            "public_id",
            "commande",
            "reference_commande",
            "achat",
            "reference_achat",
            "montant",
            "typePaiement",
            "date",
            "mode",
            "reference",
            "commentaire",
        )


class PaiementCreationSerializer(serializers.Serializer):
    operation = serializers.ChoiceField(choices=("order", "purchase"))
    public_id = serializers.UUIDField()
    montant = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    typePaiement = serializers.ChoiceField(
        choices=Paiement.TypePaiement.choices,
        default=Paiement.TypePaiement.VERSEMENT,
    )
    date = serializers.DateField(required=False, default=timezone.localdate)
    mode = serializers.ChoiceField(choices=Paiement.Mode.choices, default=Paiement.Mode.ESPECES)
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True)
    commentaire = serializers.CharField(max_length=255, required=False, allow_blank=True)
