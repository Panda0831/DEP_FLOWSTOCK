import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Produit


def nouvelle_reference_commande():
    return f"CMD-{uuid.uuid4().hex[:12].upper()}"


class Client(models.Model):
    idClient = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nomClient = models.CharField(max_length=120)
    contact = models.CharField(max_length=120, blank=True)
    adresse = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "Client"


class Commande(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        CONFIRMEE = "confirmee", "Confirmée"
        EN_PREPARATION = "en_preparation", "En préparation"
        EXPEDIEE = "expediee", "Expédiée"
        LIVREE = "livree", "Livrée"
        ANNULLEE = "annulee", "Annulée"
        RETOURNEE = "retournee", "Retournée"

    idCommande = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.CharField(max_length=32, unique=True, default=nouvelle_reference_commande)
    idClient = models.ForeignKey(
        Client, on_delete=models.PROTECT, db_column="idClient", related_name="commandes"
    )
    idUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="idUser",
        related_name="commandes",
    )
    date = models.DateField(default=timezone.localdate)
    statut = models.CharField(max_length=15, choices=Statut.choices, default=Statut.EN_ATTENTE)
    remise = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fraisLivraison = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "Commande"
        ordering = ("-date", "-idCommande")
        constraints = [
            models.CheckConstraint(condition=Q(remise__gte=0), name="cmd_remise_nonneg"),
            models.CheckConstraint(
                condition=Q(fraisLivraison__gte=0),
                name="cmd_frais_liv_nonneg",
            ),
        ]

    @property
    def montant_total(self):
        sous_total = sum(
            (ligne.quantite * ligne.prixUnitaire for ligne in self.lignes.all()),
            start=0,
        )
        return sous_total - self.remise + self.fraisLivraison


class LigneCommande(models.Model):
    idLigne = models.BigAutoField(primary_key=True)
    idCommande = models.ForeignKey(
        Commande, on_delete=models.PROTECT, db_column="idCommande", related_name="lignes"
    )
    idProduit = models.ForeignKey(
        Produit, on_delete=models.PROTECT, db_column="idProduit", related_name="lignes_commande"
    )
    quantite = models.PositiveIntegerField()
    prixUnitaire = models.DecimalField(max_digits=12, decimal_places=2)
    coutUnitaire = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "LigneCommande"
        constraints = [
            models.UniqueConstraint(
                fields=("idCommande", "idProduit"),
                name="ligne_commande_produit_unique",
            ),
            models.CheckConstraint(
                condition=Q(quantite__gt=0),
                name="ligne_commande_quantite_positive",
            ),
        ]


class Livraison(models.Model):
    class Statut(models.TextChoices):
        EN_COURS = "en_cours", "En cours"
        EN_PREPARATION = "en_preparation", "En préparation"
        EXPEDIEE = "expediee", "Expédiée"
        LIVREE = "livree", "Livrée"
        ECHEC = "echec", "Échec"
        RETOURNEE = "retournee", "Retournée"
        ANNULEE = "annulee", "Annulée"

    idLivraison = models.BigAutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    idCommande = models.OneToOneField(
        Commande, on_delete=models.PROTECT, db_column="idCommande", related_name="livraison"
    )
    adresse = models.CharField(max_length=255, blank=True)
    commentaire = models.CharField(max_length=255, blank=True)
    dateExpedition = models.DateField(blank=True, null=True)
    dateLivraison = models.DateField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_COURS)
    cout = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fraisFacture = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "Livraison"
        constraints = [
            models.CheckConstraint(condition=Q(cout__gte=0), name="livraison_cout_non_negatif"),
            models.CheckConstraint(
                condition=Q(fraisFacture__gte=0),
                name="livraison_frais_non_negatif",
            ),
        ]
