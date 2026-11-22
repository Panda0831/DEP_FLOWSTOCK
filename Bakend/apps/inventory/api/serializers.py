from rest_framework import serializers

from ..models import Mouvement


class MouvementSerializer(serializers.ModelSerializer):
    produit = serializers.UUIDField(source="idProduit.public_id", read_only=True)

    class Meta:
        model = Mouvement
        fields = (
            "public_id",
            "produit",
            "typeMouvement",
            "quantite",
            "date",
            "motif",
            "referenceOperation",
        )


class MouvementCreationSerializer(serializers.Serializer):
    product = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    motif = serializers.CharField(max_length=255, required=False, allow_blank=True)


class StockSerializer(serializers.Serializer):
    public_id = serializers.UUIDField()
    nomProduit = serializers.CharField()
    stock = serializers.IntegerField()
    seuilAlerte = serializers.IntegerField()
