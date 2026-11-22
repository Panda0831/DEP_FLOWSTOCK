from django.core.validators import MinValueValidator
from rest_framework import serializers

from apps.accounts.permissions import has_role

from ..models import Categorie, Fournisseur, Produit


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ("public_id", "nomCategorie")
        read_only_fields = ("public_id",)


class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = ("public_id", "nomFournisseur")
        read_only_fields = ("public_id",)


class ProduitSerializer(serializers.ModelSerializer):
    idCategorie = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Categorie.objects.all(), required=False, allow_null=True
    )
    idFournisseur = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Fournisseur.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Produit
        fields = (
            "public_id",
            "nomProduit",
            "prixVente",
            "prixAchat",
            "seuilAlerte",
            "photo",
            "isActif",
            "idCategorie",
            "idFournisseur",
        )
        read_only_fields = ("public_id",)
        extra_kwargs = {
            "prixVente": {"validators": [MinValueValidator(0)]},
            "prixAchat": {"validators": [MinValueValidator(0)]},
        }

    def validate_seuilAlerte(self, value):
        if value < 0:
            raise serializers.ValidationError("Le seuil d'alerte doit être positif ou nul.")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and not has_role(request.user, "ADMIN"):
            data.pop("prixAchat", None)
        return data
