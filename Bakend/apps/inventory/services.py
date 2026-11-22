from django.db import transaction
from django.db.models import Q, Sum
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Produit

from .models import Mouvement


def stock_actuel(produit):
    result = produit.mouvements.aggregate(
        entrees=Sum(
            "quantite",
            filter=Q(
                typeMouvement__in=(
                    "entree",
                    "retour_client",
                    "ajustement_positif",
                )
            ),
        ),
        sorties=Sum(
            "quantite",
            filter=Q(
                typeMouvement__in=(
                    "sortie",
                    "perte",
                    "retour_fournisseur",
                    "ajustement_negatif",
                )
            ),
        ),
    )
    return (result["entrees"] or 0) - (result["sorties"] or 0)


@transaction.atomic
def enregistrer_mouvement(
    *,
    public_id,
    type_mouvement,
    quantite,
    user,
    id_commande=None,
    motif="",
    reference_operation="",
):
    try:
        produit = Produit.objects.select_for_update().get(public_id=public_id)
    except Produit.DoesNotExist:
        raise ValidationError({"detail": "Produit introuvable."})
    if quantite <= 0:
        raise ValidationError({"quantite": "La quantité doit être strictement positive."})
    if type_mouvement in (
        "sortie",
        "perte",
        "retour_fournisseur",
        "ajustement_negatif",
    ) and stock_actuel(produit) < quantite:
        raise ValidationError({"detail": "Le stock disponible est insuffisant."})
    mouvement = Mouvement.objects.create(
        idProduit=produit,
        typeMouvement=type_mouvement,
        quantite=quantite,
        idUser=user,
        idCommande_id=id_commande,
        motif=motif,
        referenceOperation=reference_operation,
    )
    return mouvement
