import uuid

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q


def validate_photo_size(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("La photo ne peut pas dépasser 5 Mo.")


class Categorie(models.Model):
    idCategorie = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nomCategorie = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "Categorie"

    def __str__(self):
        return self.nomCategorie


class Fournisseur(models.Model):
    idFournisseur = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nomFournisseur = models.CharField(max_length=120)

    class Meta:
        db_table = "Fournisseur"

    def __str__(self):
        return self.nomFournisseur


class Produit(models.Model):
    idProduit = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nomProduit = models.CharField(max_length=150)
    prixVente = models.DecimalField(max_digits=12, decimal_places=2)
    prixAchat = models.DecimalField(max_digits=12, decimal_places=2)
    seuilAlerte = models.PositiveIntegerField(default=0)
    photo = models.ImageField(
        upload_to="produits/",
        blank=True,
        validators=[FileExtensionValidator(("jpg", "jpeg", "png", "webp")), validate_photo_size],
    )
    isActif = models.BooleanField(default=True)
    idCategorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        db_column="idCategorie",
        related_name="produits",
        blank=True,
        null=True,
    )
    idFournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.PROTECT,
        db_column="idFournisseur",
        related_name="produits",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "Produit"
        ordering = ("nomProduit",)
        constraints = [
            models.CheckConstraint(
                condition=Q(prixVente__gte=0),
                name="produit_prix_vente_non_negatif",
            ),
            models.CheckConstraint(
                condition=Q(prixAchat__gte=0),
                name="produit_prix_achat_non_negatif",
            ),
        ]

    def __str__(self):
        return self.nomProduit
