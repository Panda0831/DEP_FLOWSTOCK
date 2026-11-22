import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Depense(models.Model):
    idDepense = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    date = models.DateField(default=timezone.localdate)
    libelle = models.CharField(max_length=150)
    montant = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "Depense"
        ordering = ("-date",)
        constraints = [
            models.CheckConstraint(
                condition=Q(montant__gte=0),
                name="depense_montant_non_negatif",
            )
        ]


class Paiement(models.Model):
    class TypePaiement(models.TextChoices):
        VERSEMENT = "versement", "Versement"
        REMBOURSEMENT = "remboursement", "Remboursement"

    class Mode(models.TextChoices):
        ESPECES = "especes", "Espèces"
        MVOLA = "mvola", "MVola"
        ORANGE_MONEY = "orange_money", "Orange Money"
        AIRTEL_MONEY = "airtel_money", "Airtel Money"
        VIREMENT = "virement", "Virement bancaire"
        AUTRE = "autre", "Autre"

    idPaiement = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    idCommande = models.ForeignKey(
        "sales.Commande",
        on_delete=models.PROTECT,
        related_name="paiements",
        blank=True,
        null=True,
    )
    idAchat = models.ForeignKey(
        "purchasing.Achat",
        on_delete=models.PROTECT,
        related_name="paiements",
        blank=True,
        null=True,
    )
    idUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="paiements_enregistres",
    )
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    typePaiement = models.CharField(
        max_length=16,
        choices=TypePaiement.choices,
        default=TypePaiement.VERSEMENT,
    )
    date = models.DateField(default=timezone.localdate)
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.ESPECES)
    reference = models.CharField(max_length=120, blank=True)
    commentaire = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Paiement"
        ordering = ("-date", "-idPaiement")
        constraints = [
            models.CheckConstraint(condition=Q(montant__gt=0), name="paiement_montant_positif"),
            models.CheckConstraint(
                condition=(
                    Q(idCommande__isnull=False, idAchat__isnull=True)
                    | Q(idCommande__isnull=True, idAchat__isnull=False)
                ),
                name="paiement_operation_unique",
            ),
        ]
