import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Produit


class Mouvement(models.Model):
    class TypeMouvement(models.TextChoices):
        ENTREE = "entree", "Entrée"
        SORTIE = "sortie", "Sortie"
        PERTE = "perte", "Perte"
        RETOUR_CLIENT = "retour_client", "Retour client"
        RETOUR_FOURNISSEUR = "retour_fournisseur", "Retour fournisseur"
        AJUSTEMENT_POSITIF = "ajustement_positif", "Ajustement positif"
        AJUSTEMENT_NEGATIF = "ajustement_negatif", "Ajustement négatif"

    idMouvement = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    idProduit = models.ForeignKey(
        Produit, on_delete=models.PROTECT, db_column="idProduit", related_name="mouvements"
    )
    typeMouvement = models.CharField(max_length=24, choices=TypeMouvement.choices)
    quantite = models.PositiveIntegerField()
    date = models.DateField(default=timezone.localdate)
    motif = models.CharField(max_length=255, blank=True)
    referenceOperation = models.CharField(max_length=64, blank=True)
    idUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="idUser",
        related_name="mouvements",
    )
    idCommande = models.ForeignKey(
        "sales.Commande",
        on_delete=models.PROTECT,
        db_column="idCommande",
        related_name="mouvements",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "Mouvement"
        ordering = ("-date", "-idMouvement")
        constraints = [
            models.CheckConstraint(
                condition=Q(quantite__gt=0),
                name="mouvement_quantite_positive",
            )
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Un mouvement de stock est immuable")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Un mouvement de stock ne peut pas être supprimé")
