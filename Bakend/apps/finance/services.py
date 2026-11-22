from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum
from django.db.models.functions import TruncMonth
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Produit
from apps.inventory.services import stock_actuel
from apps.sales.models import Commande, LigneCommande, Livraison

from .models import Depense, Paiement

ZERO = Decimal("0.00")


def _month_date(value):
    month = value.date() if isinstance(value, datetime) else value
    return month.replace(day=1)


def commandes_livrees(debut, fin):
    return Commande.objects.filter(
        statut__in=(Commande.Statut.CONFIRMEE, Commande.Statut.LIVREE),
        livraison__statut=Livraison.Statut.LIVREE,
        livraison__dateLivraison__range=(debut, fin),
    )


def lignes_livrees(debut, fin):
    return LigneCommande.objects.filter(idCommande__in=commandes_livrees(debut, fin))


def calculer_resume(debut, fin):
    lignes = lignes_livrees(debut, fin).aggregate(
        chiffre_affaires=Sum(F("quantite") * F("prixUnitaire")),
        marge=Sum(F("quantite") * (F("prixUnitaire") - F("coutUnitaire"))),
    )
    livraisons = Livraison.objects.filter(
        idCommande__in=commandes_livrees(debut, fin),
        statut=Livraison.Statut.LIVREE,
    ).aggregate(frais=Sum("fraisFacture"), cout=Sum("cout"))
    depenses = (
        Depense.objects.filter(date__range=(debut, fin)).aggregate(total=Sum("montant"))["total"]
        or ZERO
    )
    frais = livraisons["frais"] or ZERO
    brut = (lignes["marge"] or ZERO) + frais - (livraisons["cout"] or ZERO)
    return {
        "chiffre_affaires": (lignes["chiffre_affaires"] or ZERO) + frais,
        "benefice_brut": brut,
        "depenses": depenses,
        "benefice_net": brut - depenses,
        "commandes_livrees": commandes_livrees(debut, fin).count(),
    }


def rapport_produits(debut, fin):
    return list(
        lignes_livrees(debut, fin)
        .values("idProduit__public_id", "idProduit__nomProduit")
        .annotate(
            quantite_vendue=Sum("quantite"),
            chiffre_affaires=Sum(F("quantite") * F("prixUnitaire")),
            benefice_brut=Sum(F("quantite") * (F("prixUnitaire") - F("coutUnitaire"))),
        )
        .order_by("idProduit__nomProduit")
    )


def rapport_commandes(debut, fin):
    commandes = commandes_livrees(debut, fin).prefetch_related("lignes", "livraison", "idClient")
    rows = []
    for commande in commandes:
        lignes = list(commande.lignes.all())
        livraison = commande.livraison
        ca = sum((ligne.quantite * ligne.prixUnitaire for ligne in lignes), ZERO)
        marge = sum(
            (ligne.quantite * (ligne.prixUnitaire - ligne.coutUnitaire) for ligne in lignes),
            ZERO,
        )
        rows.append(
            {
                "public_id": str(commande.public_id),
                "client": commande.idClient.nomClient,
                "date_livraison": livraison.dateLivraison,
                "chiffre_affaires": ca + livraison.fraisFacture,
                "benefice": marge + livraison.fraisFacture - livraison.cout,
            }
        )
    return rows


def rapport_mensuel(debut, fin):
    resultats = defaultdict(
        lambda: {
            "benefice_brut": ZERO,
            "depenses": ZERO,
        }
    )
    lignes = (
        lignes_livrees(debut, fin)
        .annotate(mois=TruncMonth("idCommande__livraison__dateLivraison"))
        .values("mois")
        .annotate(marge=Sum(F("quantite") * (F("prixUnitaire") - F("coutUnitaire"))))
    )
    for row in lignes:
        if row["mois"]:
            resultats[_month_date(row["mois"])]["benefice_brut"] += row["marge"] or ZERO
    livraisons = (
        Livraison.objects.filter(
            idCommande__in=commandes_livrees(debut, fin),
            statut=Livraison.Statut.LIVREE,
        )
        .annotate(mois=TruncMonth("dateLivraison"))
        .values("mois")
        .annotate(frais=Sum("fraisFacture"), cout=Sum("cout"))
    )
    for row in livraisons:
        if row["mois"]:
            resultats[_month_date(row["mois"])]["benefice_brut"] += (row["frais"] or ZERO) - (
                row["cout"] or ZERO
            )
    depenses = (
        Depense.objects.filter(date__range=(debut, fin))
        .annotate(mois=TruncMonth("date"))
        .values("mois")
        .annotate(total=Sum("montant"))
    )
    for row in depenses:
        if row["mois"]:
            resultats[_month_date(row["mois"])]["depenses"] += row["total"] or ZERO
    return [
        {
            "mois": mois,
            **montants,
            "benefice_net": montants["benefice_brut"] - montants["depenses"],
        }
        for mois, montants in sorted(resultats.items())
    ]


def produits_en_alerte():
    resultats = []
    for produit in Produit.objects.filter(isActif=True).order_by("nomProduit"):
        stock = stock_actuel(produit)
        if stock <= produit.seuilAlerte:
            resultats.append(
                {
                    "public_id": str(produit.public_id),
                    "nomProduit": produit.nomProduit,
                    "stock": stock,
                    "seuilAlerte": produit.seuilAlerte,
                }
            )
    return resultats


def montant_paye(operation):
    paiements = operation.paiements
    versements = paiements.filter(
        typePaiement=Paiement.TypePaiement.VERSEMENT
    ).aggregate(total=Sum("montant"))["total"] or ZERO
    remboursements = paiements.filter(
        typePaiement=Paiement.TypePaiement.REMBOURSEMENT
    ).aggregate(total=Sum("montant"))["total"] or ZERO
    return max(versements - remboursements, ZERO)


def montant_restant(operation):
    return max(operation.montant_total - montant_paye(operation), ZERO)


@transaction.atomic
def enregistrer_paiement(
    *,
    type_operation,
    public_id,
    montant,
    date,
    mode,
    reference,
    commentaire,
    user,
    type_paiement=Paiement.TypePaiement.VERSEMENT,
):
    from apps.purchasing.models import Achat
    from apps.sales.models import Commande

    if type_operation == "purchase":
        if type_paiement == Paiement.TypePaiement.REMBOURSEMENT:
            raise ValidationError({"typePaiement": "Le remboursement fournisseur n'est pas pris en charge."})
        try:
            operation = Achat.objects.select_for_update().get(public_id=public_id)
        except Achat.DoesNotExist:
            raise ValidationError({"purchase": "Achat introuvable."})
        if operation.statut == Achat.Statut.ANNULE:
            raise ValidationError({"detail": "Un achat annulé ne peut pas recevoir de paiement."})
        lien = {"idAchat": operation}
    elif type_operation == "order":
        try:
            operation = Commande.objects.select_for_update().get(public_id=public_id)
        except Commande.DoesNotExist:
            raise ValidationError({"order": "Commande introuvable."})
        if operation.statut == Commande.Statut.ANNULLEE:
            raise ValidationError({"detail": "Cette commande ne peut pas recevoir de paiement."})
        if (
            operation.statut == Commande.Statut.RETOURNEE
            and type_paiement != Paiement.TypePaiement.REMBOURSEMENT
        ):
            raise ValidationError({"detail": "Une commande retournée accepte uniquement un remboursement."})
        lien = {"idCommande": operation}
    else:
        raise ValidationError({"operation": "Type d'opération invalide."})

    if type_paiement == Paiement.TypePaiement.REMBOURSEMENT:
        if not isinstance(operation, Commande) or operation.statut != Commande.Statut.RETOURNEE:
            raise ValidationError({"detail": "Un remboursement est possible après le retour d'une commande."})
        disponible = montant_paye(operation)
        if montant > disponible:
            raise ValidationError({"montant": f"Le remboursement dépasse les paiements reçus ({disponible})."})
    else:
        restant = montant_restant(operation)
        if montant > restant:
            raise ValidationError({"montant": f"Le paiement dépasse le solde restant ({restant})."})
    if montant <= 0:
        raise ValidationError({"montant": "Le montant doit être supérieur à zéro."})
    paiement = Paiement.objects.create(
        **lien,
        idUser=user,
        montant=montant,
        typePaiement=type_paiement,
        date=date,
        mode=mode,
        reference=reference,
        commentaire=commentaire,
    )
    if type_operation == "purchase":
        from apps.purchasing.models import HistoriqueAchat

        HistoriqueAchat.objects.create(
            idAchat=operation,
            idUser=user,
            evenement=HistoriqueAchat.Evenement.PAIEMENT,
            referenceOperation=paiement.reference or str(paiement.public_id),
            details={"montant": str(montant), "mode": mode, "date": str(date)},
        )
    return paiement
