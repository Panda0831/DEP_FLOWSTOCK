import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Fournisseur, Produit


def nouvelle_reference_achat():
    return f"ACH-{uuid.uuid4().hex[:12].upper()}"


def nouvelle_reference_reception():
    return f"REC-{uuid.uuid4().hex[:12].upper()}"


class Achat(models.Model):
    class Obtention(models.TextChoices):
        COMMANDE = "commande", "Commande"
        ACHAT_DIRECT = "achat_direct", "Achat direct"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "À recevoir"
        PARTIEL = "partiellement_recu", "Partiellement reçu"
        RECU = "recu", "Reçu"
        ANNULE = "annule", "Annulé"

    idAchat = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.CharField(max_length=32, unique=True, default=nouvelle_reference_achat)
    idFournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.PROTECT, db_column="idFournisseur", related_name="achats"
    )
    idUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="idUser",
        related_name="achats",
    )
    dateCommande = models.DateField(default=timezone.localdate)
    lieuAchat = models.CharField(max_length=180, blank=True)
    modeObtention = models.CharField(
        max_length=16, choices=Obtention.choices, default=Obtention.COMMANDE
    )
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Achat"
        ordering = ("-dateCommande", "-idAchat")

    @property
    def montant_total(self):
        return sum(
            (ligne.quantite * ligne.prixUnitaire for ligne in self.lignes.all()),
            start=0,
        )

    @property
    def quantite_recue(self):
        return sum(ligne.quantite for ligne in self.lignes_reception.all())


class LigneAchat(models.Model):
    idLigneAchat = models.BigAutoField(primary_key=True)
    idAchat = models.ForeignKey(Achat, on_delete=models.PROTECT, related_name="lignes")
    idProduit = models.ForeignKey(
        Produit, on_delete=models.PROTECT, related_name="lignes_achat"
    )
    quantite = models.PositiveIntegerField()
    prixUnitaire = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "LigneAchat"
        constraints = [
            models.UniqueConstraint(
                fields=("idAchat", "idProduit"), name="achat_ligne_produit_unique"
            ),
            models.CheckConstraint(
                condition=Q(quantite__gt=0), name="achat_ligne_qte_positive"
            ),
            models.CheckConstraint(
                condition=Q(prixUnitaire__gte=0), name="achat_ligne_prix_nonneg"
            ),
        ]


class ReceptionAchat(models.Model):
    idReception = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.CharField(max_length=32, unique=True, default=nouvelle_reference_reception)
    idAchat = models.ForeignKey(
        Achat, on_delete=models.PROTECT, related_name="receptions"
    )
    date = models.DateField(default=timezone.localdate)
    lieu = models.CharField(max_length=180, blank=True)
    commentaire = models.CharField(max_length=255, blank=True)
    idUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="receptions_achat",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ReceptionAchat"
        ordering = ("-date", "-idReception")


class LigneReceptionAchat(models.Model):
    idLigneReception = models.BigAutoField(primary_key=True)
    idReception = models.ForeignKey(
        ReceptionAchat, on_delete=models.PROTECT, related_name="lignes"
    )
    idLigneAchat = models.ForeignKey(
        LigneAchat, on_delete=models.PROTECT, related_name="lignes_reception"
    )
    quantite = models.PositiveIntegerField()

    class Meta:
        db_table = "LigneReceptionAchat"
        constraints = [
            models.UniqueConstraint(
                fields=("idReception", "idLigneAchat"),
                name="rec_achat_ligne_unique",
            ),
            models.CheckConstraint(
                condition=Q(quantite__gt=0), name="rec_achat_qte_positive"
            ),
        ]


class HistoriqueAchat(models.Model):
    class Evenement(models.TextChoices):
        CREATION = "creation", "Création"
        MODIFICATION = "modification", "Modification"
        RECEPTION = "reception", "Réception"
        PAIEMENT = "paiement", "Paiement"
        ANNULATION = "annulation", "Annulation"
        RETOUR_FOURNISSEUR = "retour_fournisseur", "Retour fournisseur"

    idHistorique = models.BigAutoField(primary_key=True)
    idAchat = models.ForeignKey(Achat, on_delete=models.PROTECT, related_name="historique")
    idUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="historique_achats",
    )
    evenement = models.CharField(max_length=24, choices=Evenement.choices)
    date = models.DateTimeField(auto_now_add=True)
    referenceOperation = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "HistoriqueAchat"
        ordering = ("-date", "-idHistorique")
