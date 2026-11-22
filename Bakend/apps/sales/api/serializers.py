from rest_framework import serializers

from apps.accounts.permissions import has_role
from apps.finance.api.serializers import PaiementSerializer
from apps.finance.services import montant_paye, montant_restant

from ..models import Client, Commande, LigneCommande, Livraison


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ("public_id", "nomClient", "contact", "adresse")

    def validate_nomClient(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le nom du client est obligatoire.")
        return value


class LigneCommandeSerializer(serializers.ModelSerializer):
    product = serializers.UUIDField(source="idProduit.public_id", read_only=True)
    coutUnitaire = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = LigneCommande
        fields = ("product", "quantite", "prixUnitaire", "coutUnitaire")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and not has_role(request.user, "ADMIN"):
            data.pop("coutUnitaire", None)
        return data


class CommandeSerializer(serializers.ModelSerializer):
    client = serializers.UUIDField(source="idClient.public_id", read_only=True)
    lignes = LigneCommandeSerializer(many=True, read_only=True)
    paiements = PaiementSerializer(many=True, read_only=True)
    montant_total = serializers.SerializerMethodField()
    montant_paye = serializers.SerializerMethodField()
    solde_restant = serializers.SerializerMethodField()

    class Meta:
        model = Commande
        fields = (
            "public_id",
            "reference",
            "client",
            "date",
            "statut",
            "remise",
            "fraisLivraison",
            "montant_total",
            "montant_paye",
            "solde_restant",
            "paiements",
            "lignes",
        )
        read_only_fields = ("public_id", "date", "statut")

    def get_montant_total(self, obj):
        return obj.montant_total

    def get_montant_paye(self, obj):
        return montant_paye(obj)

    def get_solde_restant(self, obj):
        return montant_restant(obj)


class CommandeCreationSerializer(serializers.Serializer):
    client = serializers.UUIDField()
    items = serializers.ListField(child=serializers.DictField(), allow_empty=False)
    remise = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, default=0)
    fraisLivraison = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, default=0
    )

    def validate_items(self, items):
        produits = set()
        cleaned = []
        for item in items:
            try:
                product = serializers.UUIDField().run_validation(item["product"])
                quantity = serializers.IntegerField(min_value=1).run_validation(item["quantity"])
            except (KeyError, TypeError, ValueError, serializers.ValidationError):
                raise serializers.ValidationError("Chaque ligne doit contenir product et quantity.")
            if product in produits:
                raise serializers.ValidationError(
                    "Un produit ne peut apparaître qu'une seule fois dans la commande."
                )
            produits.add(product)
            cleaned.append({"product": product, "quantity": quantity})
        return cleaned


class CommandeUpdateSerializer(serializers.Serializer):
    client = serializers.UUIDField(required=False)
    items = serializers.ListField(child=serializers.DictField(), required=False, allow_empty=False)
    remise = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False)
    fraisLivraison = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False
    )

    def validate_items(self, items):
        return CommandeCreationSerializer().validate_items(items)


class LivraisonSerializer(serializers.ModelSerializer):
    commande = serializers.UUIDField(write_only=True, required=False)
    reference_commande = serializers.CharField(source="idCommande.reference", read_only=True)
    client = serializers.CharField(source="idCommande.idClient.nomClient", read_only=True)

    class Meta:
        model = Livraison
        fields = (
            "public_id",
            "commande",
            "reference_commande",
            "client",
            "adresse",
            "commentaire",
            "dateExpedition",
            "dateLivraison",
            "statut",
            "cout",
            "fraisFacture",
        )
        read_only_fields = ("public_id", "statut", "dateExpedition", "dateLivraison")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["commande"] = str(instance.idCommande.public_id)
        return data

    def create(self, validated_data):
        commande_public_id = validated_data.pop("commande", None)
        if commande_public_id is None:
            raise serializers.ValidationError({"commande": "Ce champ est obligatoire."})
        try:
            commande = Commande.objects.get(public_id=commande_public_id)
        except Commande.DoesNotExist:
            raise serializers.ValidationError({"commande": "Commande introuvable."})
        if hasattr(commande, "livraison"):
            raise serializers.ValidationError(
                {"commande": "Cette commande possède déjà une livraison."}
            )
        if commande.statut != Commande.Statut.CONFIRMEE:
            raise serializers.ValidationError(
                {"commande": "Une livraison ne peut être créée que pour une commande confirmée."}
            )
        validated_data["adresse"] = validated_data.get("adresse") or commande.idClient.adresse
        return Livraison.objects.create(idCommande=commande, **validated_data)

    def update(self, instance, validated_data):
        if "commande" in validated_data:
            raise serializers.ValidationError(
                {"commande": "La commande d'une livraison ne peut pas être modifiée."}
            )
        return super().update(instance, validated_data)

    def validate(self, attrs):
        if attrs.get("statut") == "livree" and not attrs.get("dateLivraison"):
            instance_date = getattr(self.instance, "dateLivraison", None)
            if not instance_date:
                raise serializers.ValidationError(
                    {"dateLivraison": "Une livraison livrée doit avoir une date."}
                )
        for field in ("cout", "fraisFacture"):
            if field in attrs and attrs[field] < 0:
                raise serializers.ValidationError({field: "Le montant doit être positif ou nul."})
        return attrs
