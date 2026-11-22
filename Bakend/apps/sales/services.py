from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Produit
from apps.inventory.models import Mouvement
from apps.inventory.services import stock_actuel

from .models import Commande, LigneCommande


@transaction.atomic
def creer_commande(*, client, items, user, remise=Decimal("0"), frais_livraison=Decimal("0")):
    commande = Commande.objects.create(
        idClient=client,
        idUser=user,
        remise=remise,
        fraisLivraison=frais_livraison,
    )
    for item in items:
        try:
            produit = Produit.objects.get(public_id=item["product"], isActif=True)
        except Produit.DoesNotExist:
            raise ValidationError({"detail": "Produit introuvable ou désactivé."})
        LigneCommande.objects.create(
            idCommande=commande,
            idProduit=produit,
            quantite=item["quantity"],
            prixUnitaire=produit.prixVente,
            coutUnitaire=produit.prixAchat,
        )
    sous_total = sum(
        (ligne.quantite * ligne.prixUnitaire for ligne in commande.lignes.all()),
        start=Decimal("0.00"),
    )
    if remise > sous_total:
        raise ValidationError({"remise": "La remise ne peut pas dépasser le montant des produits."})
    return commande


@transaction.atomic
def modifier_commande(
    *, commande, client=None, items=None, remise=None, frais_livraison=None
):
    commande = Commande.objects.select_for_update().get(pk=commande.pk)
    if commande.statut != Commande.Statut.EN_ATTENTE:
        raise ValidationError({"detail": "Seule une commande en attente peut être modifiée."})
    if client is not None:
        commande.idClient = client
        commande.save(update_fields=("idClient",))
    if items is not None:
        produits = []
        for item in items:
            try:
                produit = Produit.objects.get(public_id=item["product"], isActif=True)
            except Produit.DoesNotExist:
                raise ValidationError({"detail": "Produit introuvable ou désactivé."})
            produits.append((produit, item["quantity"]))
        commande.lignes.all().delete()
        LigneCommande.objects.bulk_create(
            [
                LigneCommande(
                    idCommande=commande,
                    idProduit=produit,
                    quantite=quantite,
                    prixUnitaire=produit.prixVente,
                    coutUnitaire=produit.prixAchat,
                )
                for produit, quantite in produits
            ]
        )
    if remise is not None:
        commande.remise = remise
    if frais_livraison is not None:
        commande.fraisLivraison = frais_livraison
    if remise is not None or frais_livraison is not None or items is not None:
        sous_total = sum(
            (ligne.quantite * ligne.prixUnitaire for ligne in commande.lignes.all()),
            start=Decimal("0.00"),
        )
        if commande.remise > sous_total:
            raise ValidationError(
                {"remise": "La remise ne peut pas dépasser le montant des produits."}
            )
        commande.save(update_fields=("remise", "fraisLivraison"))
    return commande


@transaction.atomic
def confirmer_commande(*, commande, user):
    commande = Commande.objects.select_for_update().select_related("idClient").get(pk=commande.pk)
    if commande.statut == Commande.Statut.CONFIRMEE:
        raise ValidationError({"detail": "Cette commande est déjà confirmée."})
    if commande.statut != Commande.Statut.EN_ATTENTE:
        raise ValidationError({"detail": "Cette commande ne peut pas être confirmée."})
    for ligne in (
        LigneCommande.objects.select_for_update()
        .filter(idCommande=commande)
        .select_related("idProduit")
    ):
        produit = Produit.objects.select_for_update().get(pk=ligne.idProduit_id)
        if stock_actuel(produit) < ligne.quantite:
            raise ValidationError(
                {"detail": "Le stock disponible est insuffisant.", "code": "stock_insuffisant"}
            )
    for ligne in LigneCommande.objects.filter(idCommande=commande).select_related("idProduit"):
        Mouvement.objects.create(
            idProduit=ligne.idProduit,
            typeMouvement="sortie",
            quantite=ligne.quantite,
            idUser=user,
            idCommande=commande,
        )
    commande.statut = Commande.Statut.CONFIRMEE
    commande.save(update_fields=("statut",))
    return commande


@transaction.atomic
def annuler_commande(*, commande, user):
    commande = Commande.objects.select_for_update().get(pk=commande.pk)
    if commande.statut == Commande.Statut.ANNULLEE:
        raise ValidationError({"detail": "Cette commande est déjà annulée."})
    if commande.statut in (Commande.Statut.EXPEDIEE, Commande.Statut.LIVREE, Commande.Statut.RETOURNEE):
        raise ValidationError(
            {"detail": "Une commande expédiée doit suivre le processus de retour."}
        )
    if commande.statut in (
        Commande.Statut.CONFIRMEE,
        Commande.Statut.EN_PREPARATION,
    ):
        livraison = getattr(commande, "livraison", None)
        if livraison and livraison.statut in (
            livraison.Statut.EXPEDIEE,
            livraison.Statut.LIVREE,
            livraison.Statut.RETOURNEE,
        ):
            raise ValidationError(
                {"detail": "Une livraison expédiée doit suivre le processus de retour."}
            )
        for ligne in LigneCommande.objects.filter(idCommande=commande).select_related("idProduit"):
            Mouvement.objects.create(
                idProduit=ligne.idProduit,
                typeMouvement="entree",
                quantite=ligne.quantite,
                idUser=user,
                idCommande=commande,
                motif=f"Annulation de la commande {commande.reference}",
                referenceOperation=commande.reference,
            )
        if livraison:
            livraison.statut = livraison.Statut.ANNULEE
            livraison.save(update_fields=("statut",))
    commande.statut = Commande.Statut.ANNULLEE
    commande.save(update_fields=("statut",))
    return commande


@transaction.atomic
def modifier_statut_livraison(*, livraison, action, user=None):
    from django.utils import timezone

    from .models import Livraison

    livraison = (
        Livraison.objects.select_for_update()
        .select_related("idCommande")
        .get(pk=livraison.pk)
    )
    commande = Commande.objects.select_for_update().get(pk=livraison.idCommande_id)

    if action == "preparing":
        if livraison.statut not in (Livraison.Statut.EN_COURS,):
            raise ValidationError({"detail": "Cette livraison ne peut pas passer en préparation."})
        livraison.statut = Livraison.Statut.EN_PREPARATION
        commande.statut = Commande.Statut.EN_PREPARATION
    elif action == "shipped":
        if livraison.statut != Livraison.Statut.EN_PREPARATION:
            raise ValidationError({"detail": "La livraison doit être en préparation avant l'envoi."})
        livraison.statut = Livraison.Statut.EXPEDIEE
        livraison.dateExpedition = timezone.localdate()
        commande.statut = Commande.Statut.EXPEDIEE
    elif action == "delivered":
        if livraison.statut not in (
            Livraison.Statut.EN_COURS,
            Livraison.Statut.EN_PREPARATION,
            Livraison.Statut.EXPEDIEE,
        ):
            raise ValidationError({"detail": "Cette livraison ne peut pas être marquée livrée."})
        livraison.statut = Livraison.Statut.LIVREE
        livraison.dateLivraison = livraison.dateLivraison or timezone.localdate()
        commande.statut = Commande.Statut.LIVREE
    elif action == "failed":
        if livraison.statut in (Livraison.Statut.LIVREE, Livraison.Statut.RETOURNEE):
            raise ValidationError({"detail": "Une livraison terminée ne peut pas être mise en échec."})
        livraison.statut = Livraison.Statut.ECHEC
    elif action == "retry":
        if livraison.statut != Livraison.Statut.ECHEC:
            raise ValidationError({"detail": "Seule une livraison en échec peut être relancée."})
        livraison.statut = Livraison.Statut.EN_COURS
        livraison.dateExpedition = None
        commande.statut = Commande.Statut.CONFIRMEE
    elif action == "returned":
        if livraison.statut != Livraison.Statut.LIVREE:
            raise ValidationError({"detail": "Seule une commande livrée peut être retournée."})
        for ligne in LigneCommande.objects.filter(idCommande=commande).select_related("idProduit"):
            Mouvement.objects.create(
                idProduit=ligne.idProduit,
                typeMouvement=Mouvement.TypeMouvement.RETOUR_CLIENT,
                quantite=ligne.quantite,
                idUser=user,
                idCommande=commande,
                motif=f"Retour client de la commande {commande.reference}",
                referenceOperation=commande.reference,
            )
        livraison.statut = Livraison.Statut.RETOURNEE
        commande.statut = Commande.Statut.RETOURNEE
    else:
        raise ValidationError({"action": "Action de livraison inconnue."})

    livraison.save(update_fields=("statut", "dateExpedition", "dateLivraison"))
    commande.save(update_fields=("statut",))
    return livraison
