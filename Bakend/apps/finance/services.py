from collections import defaultdict
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import F, Sum
from django.db.models.functions import TruncMonth
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Produit
from apps.inventory.models import Mouvement
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
    remises = commandes_livrees(debut, fin).aggregate(total=Sum("remise"))["total"] or ZERO
    depenses = (
        Depense.objects.filter(date__range=(debut, fin)).aggregate(total=Sum("montant"))["total"]
        or ZERO
    )
    frais = livraisons["frais"] or ZERO
    ventes_produits = lignes["chiffre_affaires"] or ZERO
    cout_produits = ventes_produits - (lignes["marge"] or ZERO)
    cout_livraisons = livraisons["cout"] or ZERO
    brut = (lignes["marge"] or ZERO) - remises + frais - cout_livraisons
    return {
        "chiffre_affaires": ventes_produits - remises + frais,
        "ventes_produits": ventes_produits,
        "remises": remises,
        "frais_livraison_factures": frais,
        "cout_produits": cout_produits,
        "cout_livraisons": cout_livraisons,
        "benefice_brut": brut,
        "depenses": depenses,
        "benefice_net": brut - depenses,
        "commandes_livrees": commandes_livrees(debut, fin).count(),
    }


def rapport_produits(debut, fin):
    resultats = {}
    commandes = commandes_livrees(debut, fin).prefetch_related("lignes__idProduit")
    for commande in commandes:
        lignes = list(commande.lignes.all())
        sous_total = sum((ligne.quantite * ligne.prixUnitaire for ligne in lignes), ZERO)
        remise_restante = commande.remise
        for index, ligne in enumerate(lignes):
            ca_ligne = ligne.quantite * ligne.prixUnitaire
            if index == len(lignes) - 1:
                remise_ligne = remise_restante
            elif sous_total:
                remise_ligne = (commande.remise * ca_ligne / sous_total).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                remise_restante -= remise_ligne
            else:
                remise_ligne = ZERO
            ca_net = ca_ligne - remise_ligne
            row = resultats.setdefault(
                ligne.idProduit_id,
                {
                    "idProduit__public_id": ligne.idProduit.public_id,
                    "idProduit__nomProduit": ligne.idProduit.nomProduit,
                    "quantite_vendue": 0,
                    "chiffre_affaires": ZERO,
                    "benefice_brut": ZERO,
                },
            )
            row["quantite_vendue"] += ligne.quantite
            row["chiffre_affaires"] += ca_net
            row["benefice_brut"] += ca_net - ligne.quantite * ligne.coutUnitaire
    return sorted(resultats.values(), key=lambda row: row["idProduit__nomProduit"])


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
                "chiffre_affaires": ca - commande.remise + livraison.fraisFacture,
                "benefice": marge - commande.remise + livraison.fraisFacture - livraison.cout,
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
    remises = (
        commandes_livrees(debut, fin)
        .annotate(mois=TruncMonth("livraison__dateLivraison"))
        .values("mois")
        .annotate(total=Sum("remise"))
    )
    for row in remises:
        if row["mois"]:
            resultats[_month_date(row["mois"])]["benefice_brut"] -= row["total"] or ZERO
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


def montant_retourne(operation):
    from apps.purchasing.models import Achat

    if not isinstance(operation, Achat):
        return ZERO

    quantites = Mouvement.objects.filter(
        typeMouvement=Mouvement.TypeMouvement.RETOUR_FOURNISSEUR,
        referenceOperation=operation.reference,
    ).values("idProduit_id").annotate(total=Sum("quantite"))
    prix_unitaires = dict(operation.lignes.values_list("idProduit_id", "prixUnitaire"))
    return sum(
        (
            prix_unitaires[retour["idProduit_id"]] * retour["total"]
            for retour in quantites
            if retour["idProduit_id"] in prix_unitaires
        ),
        start=ZERO,
    )


def montant_total_net(operation):
    from apps.purchasing.models import Achat

    if isinstance(operation, Achat):
        return max(operation.montant_total - montant_retourne(operation), ZERO)
    return operation.montant_total


def montant_remboursable(operation):
    from apps.purchasing.models import Achat

    if not isinstance(operation, Achat):
        return ZERO
    return max(montant_paye(operation) - montant_total_net(operation), ZERO)


def montant_restant(operation):
    return max(montant_total_net(operation) - montant_paye(operation), ZERO)


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
        try:
            operation = Achat.objects.select_for_update().get(public_id=public_id)
        except Achat.DoesNotExist:
            raise ValidationError({"purchase": "Achat introuvable."})
        if operation.statut == Achat.Statut.ANNULE and type_paiement != Paiement.TypePaiement.REMBOURSEMENT:
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
        if isinstance(operation, Achat):
            if montant_retourne(operation) <= ZERO:
                raise ValidationError(
                    {"detail": "Un remboursement fournisseur est possible après un retour enregistré."}
                )
            disponible = montant_remboursable(operation)
        elif isinstance(operation, Commande) and operation.statut == Commande.Statut.RETOURNEE:
            disponible = montant_paye(operation)
        else:
            raise ValidationError(
                {"detail": "Un remboursement est possible après le retour de l'opération."}
            )
        if montant > disponible:
            raise ValidationError(
                {"montant": f"Le remboursement dépasse le montant remboursable ({disponible})."}
            )
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
            details={
                "montant": str(montant),
                "mode": mode,
                "date": str(date),
                "typePaiement": type_paiement,
            },
        )
    return paiement
