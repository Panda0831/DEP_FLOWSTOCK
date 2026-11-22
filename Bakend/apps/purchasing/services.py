from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Fournisseur, Produit
from apps.inventory.models import Mouvement
from apps.inventory.services import stock_actuel

from .models import Achat, HistoriqueAchat, LigneAchat, LigneReceptionAchat, ReceptionAchat


@transaction.atomic
def creer_achat(*, fournisseur_id, items, user, date_commande, lieu, mode_obtention):
    try:
        fournisseur = Fournisseur.objects.get(public_id=fournisseur_id)
    except Fournisseur.DoesNotExist:
        raise ValidationError({"supplier": "Fournisseur introuvable."})

    achat = Achat.objects.create(
        idFournisseur=fournisseur,
        idUser=user,
        dateCommande=date_commande,
        lieuAchat=lieu,
        modeObtention=mode_obtention,
    )
    lignes = []
    for item in items:
        try:
            produit = Produit.objects.get(public_id=item["product"], isActif=True)
        except Produit.DoesNotExist:
            raise ValidationError({"detail": "Produit introuvable ou désactivé."})
        lignes.append(
            LigneAchat(
                idAchat=achat,
                idProduit=produit,
                quantite=item["quantity"],
                prixUnitaire=item["unit_price"],
            )
        )
    LigneAchat.objects.bulk_create(lignes)
    HistoriqueAchat.objects.create(
        idAchat=achat,
        idUser=user,
        evenement=HistoriqueAchat.Evenement.CREATION,
        referenceOperation=achat.reference,
        details={
            "supplier": str(fournisseur.public_id),
            "line_count": len(lignes),
            "dateCommande": str(date_commande),
        },
    )
    return achat


@transaction.atomic
def modifier_achat(*, achat, fournisseur_id=None, items=None, date_commande=None, lieu=None, mode_obtention=None, user):
    achat = Achat.objects.select_for_update().get(pk=achat.pk)
    if achat.statut != Achat.Statut.EN_ATTENTE or achat.paiements.exists():
        raise ValidationError({"detail": "Seul un achat sans réception ni paiement peut être modifié."})

    details = {}
    if fournisseur_id is not None:
        try:
            fournisseur = Fournisseur.objects.get(public_id=fournisseur_id)
        except Fournisseur.DoesNotExist:
            raise ValidationError({"supplier": "Fournisseur introuvable."})
        achat.idFournisseur = fournisseur
        details["supplier"] = str(fournisseur.public_id)
    if date_commande is not None:
        achat.dateCommande = date_commande
        details["dateCommande"] = str(date_commande)
    if lieu is not None:
        achat.lieuAchat = lieu
        details["lieuAchat"] = lieu
    if mode_obtention is not None:
        achat.modeObtention = mode_obtention
        details["modeObtention"] = mode_obtention
    achat.save()

    if items is not None:
        resolved = []
        for item in items:
            try:
                product = Produit.objects.get(public_id=item["product"], isActif=True)
            except Produit.DoesNotExist:
                raise ValidationError({"detail": "Produit introuvable ou désactivé."})
            resolved.append((product, item["quantity"], item["unit_price"]))
        achat.lignes.all().delete()
        LigneAchat.objects.bulk_create(
            [
                LigneAchat(
                    idAchat=achat,
                    idProduit=product,
                    quantite=quantity,
                    prixUnitaire=unit_price,
                )
                for product, quantity, unit_price in resolved
            ]
        )
        details["line_count"] = len(resolved)

    HistoriqueAchat.objects.create(
        idAchat=achat,
        idUser=user,
        evenement=HistoriqueAchat.Evenement.MODIFICATION,
        referenceOperation=achat.reference,
        details=details,
    )
    return achat


@transaction.atomic
def recevoir_achat(*, achat, items, user, date, lieu="", commentaire=""):
    achat = Achat.objects.select_for_update().get(pk=achat.pk)
    if achat.statut == Achat.Statut.ANNULE:
        raise ValidationError({"detail": "Un achat annulé ne peut pas être réceptionné."})
    if achat.statut == Achat.Statut.RECU:
        raise ValidationError({"detail": "Cet achat a déjà été réceptionné en totalité."})

    reception = ReceptionAchat.objects.create(
        idAchat=achat,
        idUser=user,
        date=date,
        lieu=lieu or achat.lieuAchat,
        commentaire=commentaire,
    )
    produits_vus = set()
    for item in items:
        public_id = item["product"]
        if public_id in produits_vus:
            raise ValidationError({"items": "Un produit ne peut apparaître qu'une fois par réception."})
        produits_vus.add(public_id)
        try:
            ligne = (
                LigneAchat.objects.select_for_update()
                .select_related("idProduit")
                .get(idAchat=achat, idProduit__public_id=public_id)
            )
        except LigneAchat.DoesNotExist:
            raise ValidationError({"items": "Ce produit ne fait pas partie de l'achat."})

        deja_recu = (
            LigneReceptionAchat.objects.filter(idLigneAchat=ligne).aggregate(total=Sum("quantite"))[
                "total"
            ]
            or 0
        )
        quantite = item["quantity"]
        if deja_recu + quantite > ligne.quantite:
            raise ValidationError(
                {
                    "items": (
                        f"La quantité reçue pour {ligne.idProduit.nomProduit} dépasserait "
                        "la quantité commandée."
                    )
                }
            )
        LigneReceptionAchat.objects.create(
            idReception=reception,
            idLigneAchat=ligne,
            quantite=quantite,
        )
        Mouvement.objects.create(
            idProduit=ligne.idProduit,
            typeMouvement=Mouvement.TypeMouvement.ENTREE,
            quantite=quantite,
            date=date,
            idUser=user,
            motif=f"Réception de l'achat {achat.reference}",
            referenceOperation=reception.reference,
        )

    lignes_achat = list(achat.lignes.all())
    tous_recus = all(
        (
            LigneReceptionAchat.objects.filter(idLigneAchat=ligne).aggregate(total=Sum("quantite"))[
                "total"
            ]
            or 0
        )
        >= ligne.quantite
        for ligne in lignes_achat
    )
    achat.statut = Achat.Statut.RECU if tous_recus else Achat.Statut.PARTIEL
    achat.save(update_fields=("statut",))
    HistoriqueAchat.objects.create(
        idAchat=achat,
        idUser=user,
        evenement=HistoriqueAchat.Evenement.RECEPTION,
        referenceOperation=reception.reference,
        details={"line_count": len(items), "date": str(date)},
    )
    return reception


@transaction.atomic
def annuler_achat(*, achat, user):
    achat = Achat.objects.select_for_update().get(pk=achat.pk)
    if achat.statut == Achat.Statut.ANNULE:
        raise ValidationError({"detail": "Cet achat est déjà annulé."})
    if LigneReceptionAchat.objects.filter(idLigneAchat__idAchat=achat).exists():
        raise ValidationError(
            {"detail": "Un achat déjà réceptionné ne peut pas être annulé. Enregistrez un retour fournisseur."}
        )
    if achat.paiements.exists():
        raise ValidationError(
            {"detail": "Un achat ayant déjà reçu un paiement ne peut pas être annulé."}
        )
    achat.statut = Achat.Statut.ANNULE
    achat.save(update_fields=("statut",))
    HistoriqueAchat.objects.create(
        idAchat=achat,
        idUser=user,
        evenement=HistoriqueAchat.Evenement.ANNULATION,
        referenceOperation=achat.reference,
    )
    return achat


@transaction.atomic
def retourner_achat(*, achat, items, user, date, motif=""):
    achat = Achat.objects.select_for_update().get(pk=achat.pk)
    if achat.statut in (Achat.Statut.ANNULE, Achat.Statut.EN_ATTENTE):
        raise ValidationError({"detail": "Seul un achat déjà réceptionné peut faire l'objet d'un retour."})
    produits_vus = set()
    for item in items:
        public_id = item["product"]
        if public_id in produits_vus:
            raise ValidationError({"items": "Un produit ne peut apparaître qu'une fois par retour."})
        produits_vus.add(public_id)
        try:
            ligne = LigneAchat.objects.select_for_update().select_related("idProduit").get(
                idAchat=achat, idProduit__public_id=public_id
            )
        except LigneAchat.DoesNotExist:
            raise ValidationError({"items": "Ce produit ne fait pas partie de l'achat."})

        recu = (
            LigneReceptionAchat.objects.filter(idLigneAchat=ligne).aggregate(total=Sum("quantite"))[
                "total"
            ]
            or 0
        )
        quantite_retournee_ligne = Mouvement.objects.filter(
            idProduit=ligne.idProduit,
            typeMouvement=Mouvement.TypeMouvement.RETOUR_FOURNISSEUR,
            referenceOperation=achat.reference,
        ).aggregate(total=Sum("quantite"))["total"] or 0
        quantite = item["quantity"]
        if quantite_retournee_ligne + quantite > recu:
            raise ValidationError({"items": "Le retour dépasserait la quantité reçue pour ce produit."})
        produit = Produit.objects.select_for_update().get(pk=ligne.idProduit_id)
        if stock_actuel(produit) < quantite:
            raise ValidationError({"items": f"Stock insuffisant pour retourner {produit.nomProduit}."})
        Mouvement.objects.create(
            idProduit=produit,
            typeMouvement=Mouvement.TypeMouvement.RETOUR_FOURNISSEUR,
            quantite=quantite,
            date=date,
            idUser=user,
            motif=motif or f"Retour fournisseur pour l'achat {achat.reference}",
            referenceOperation=achat.reference,
        )

    HistoriqueAchat.objects.create(
        idAchat=achat,
        idUser=user,
        evenement=HistoriqueAchat.Evenement.RETOUR_FOURNISSEUR,
        referenceOperation=achat.reference,
        details={"line_count": len(items), "date": str(date), "motif": motif},
    )
    return achat
