"""Modèles persistants des comptes et des événements de sécurité."""

import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from apps.accounts.constantes import (
    LONGUEUR_MAXIMALE_AGENT_UTILISATEUR,
    LONGUEUR_MAXIMALE_EMAIL,
    LONGUEUR_MAXIMALE_METHODE,
    LONGUEUR_MAXIMALE_MOT_DE_PASSE,
    LONGUEUR_MAXIMALE_NOM,
    LONGUEUR_MAXIMALE_ROUTE,
    LONGUEUR_MAXIMALE_TELEPHONE,
    LONGUEUR_ROLE,
    LONGUEUR_TYPE_EVENEMENT,
)
from apps.accounts.managers import UtilisateurManager


class RoleUtilisateur(models.TextChoices):
    """Rôles exposés par l’API utilisateur."""

    ADMIN = "admin", "Administrateur"
    VENDEUR = "vendeur", "Vendeur"


class TypeEvenementSecurite(models.TextChoices):
    """Événements consignés dans le journal immuable."""

    CONNEXION_REUSSIE = "connexion_reussie", "Connexion réussie"
    CONNEXION_ECHOUEE = "connexion_echouee", "Connexion échouée"
    LISTE_UTILISATEURS_CONSULTEE = (
        "liste_utilisateurs_consultee",
        "Liste des utilisateurs consultée",
    )
    UTILISATEUR_CONSULTE = "utilisateur_consulte", "Utilisateur consulté"
    DECONNEXION = "deconnexion", "Déconnexion"
    JETON_REJETE = "jeton_rejete", "Jeton rejeté"
    UTILISATEUR_CREE = "utilisateur_cree", "Utilisateur créé"
    UTILISATEUR_MODIFIE = "utilisateur_modifie", "Utilisateur modifié"
    ROLE_MODIFIE = "role_modifie", "Rôle modifié"
    COMPTE_DESACTIVE = "compte_desactive", "Compte désactivé"
    MOT_DE_PASSE_CHANGE = "mot_de_passe_change", "Mot de passe changé"
    REINITIALISATION_DEMANDEE = "reinitialisation_demandee", "Réinitialisation demandée"
    MOT_DE_PASSE_REINITIALISE = "mot_de_passe_reinitialise", "Mot de passe réinitialisé"
    PROFIL_MODIFIE = "profil_modifie", "Profil modifié"
    ACCES_REFUSE = "acces_refuse", "Accès refusé"


class Utilisateur(AbstractBaseUser):
    """Compte StockFlow identifié publiquement par un UUID."""

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(max_length=LONGUEUR_MAXIMALE_EMAIL, unique=True)
    password = models.CharField(
        max_length=LONGUEUR_MAXIMALE_MOT_DE_PASSE,
        db_column="mot_de_passe",
    )
    nom = models.CharField(max_length=LONGUEUR_MAXIMALE_NOM)
    prenom = models.CharField(max_length=LONGUEUR_MAXIMALE_NOM)
    telephone = models.CharField(
        max_length=LONGUEUR_MAXIMALE_TELEPHONE,
        blank=True,
        default="",
        db_default="",
    )
    role = models.CharField(
        max_length=LONGUEUR_ROLE,
        choices=RoleUtilisateur.choices,
        default=RoleUtilisateur.VENDEUR,
        db_default=RoleUtilisateur.VENDEUR,
    )
    is_active = models.BooleanField(default=True, db_default=True, db_column="est_actif")
    doit_changer_mot_de_passe = models.BooleanField(default=False, db_default=False)
    is_superuser = models.BooleanField(
        default=False,
        db_default=False,
        db_column="est_super_utilisateur",
    )
    last_login = models.DateTimeField(
        blank=True,
        null=True,
        db_column="derniere_connexion",
    )
    date_dernier_changement_mot_de_passe = models.DateTimeField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True, db_default=models.functions.Now())
    date_modification = models.DateTimeField(auto_now=True, db_default=models.functions.Now())

    objects = UtilisateurManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom", "prenom"]

    class Meta:
        db_table = "utilisateurs"
        ordering = ["nom", "prenom", "id"]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="uniq_utilisateurs_email_minuscule",
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=RoleUtilisateur.values),
                name="utilisateurs_role_valide",
            ),
        ]
        indexes = [
            models.Index(fields=["role", "is_active"], name="idx_util_role_actif"),
        ]

    def __str__(self) -> str:
        """Retourne l’adresse de connexion du compte."""
        return self.email

    @property
    def is_staff(self) -> bool:
        """Autorise l’admin Django uniquement aux super-utilisateurs actifs."""
        return self.is_superuser and self.is_active

    @property
    def est_administrateur(self) -> bool:
        """Indique si le rôle métier du compte est administrateur."""
        return self.role == RoleUtilisateur.ADMIN

    def has_perm(self, perm: str, obj: object | None = None) -> bool:
        """Accorde les permissions Django uniquement aux super-utilisateurs actifs."""
        return self.is_superuser and self.is_active

    def has_module_perms(self, app_label: str) -> bool:
        """Autorise l’accès aux modules Django au super-utilisateur actif."""
        return self.is_superuser and self.is_active

    def save(self, *args, **kwargs) -> None:
        """Normalise l’e-mail avant chaque persistance."""
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class JournalSecurite(models.Model):
    """Événement de sécurité immuable conservant uniquement des métadonnées non secrètes."""

    date_evenement = models.DateTimeField(
        default=timezone.now,
        db_default=models.functions.Now(),
        editable=False,
    )
    type_evenement = models.CharField(
        max_length=LONGUEUR_TYPE_EVENEMENT,
        choices=TypeEvenementSecurite.choices,
    )
    succes = models.BooleanField()
    acteur = models.ForeignKey(
        "accounts.Utilisateur",
        on_delete=models.PROTECT,
        related_name="evenements_declenches",
        null=True,
        blank=True,
    )
    utilisateur_cible = models.ForeignKey(
        "accounts.Utilisateur",
        on_delete=models.PROTECT,
        related_name="evenements_cibles",
        null=True,
        blank=True,
    )
    email_saisi = models.EmailField(
        max_length=LONGUEUR_MAXIMALE_EMAIL,
        blank=True,
        default="",
        db_default="",
    )
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    agent_utilisateur = models.CharField(
        max_length=LONGUEUR_MAXIMALE_AGENT_UTILISATEUR,
        blank=True,
        default="",
        db_default="",
    )
    route = models.CharField(
        max_length=LONGUEUR_MAXIMALE_ROUTE,
        blank=True,
        default="",
        db_default="",
    )
    methode = models.CharField(
        max_length=LONGUEUR_MAXIMALE_METHODE,
        blank=True,
        default="",
        db_default="",
    )
    details = models.JSONField(default=dict, db_default={}, blank=True)

    class Meta:
        db_table = "journaux_securite"
        ordering = ["-date_evenement", "-id"]
        indexes = [
            models.Index(
                fields=["type_evenement", "date_evenement"],
                name="idx_journal_type_date",
            ),
            models.Index(
                fields=["acteur", "date_evenement"],
                name="idx_journal_acteur_date",
            ),
        ]

    def __str__(self) -> str:
        """Expose uniquement le type et l’horodatage de l’événement."""
        return f"{self.type_evenement} — {self.date_evenement.isoformat()}"

    def save(self, *args, **kwargs) -> None:
        """Refuse toute modification d’un événement déjà enregistré."""
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Un événement de sécurité ne peut pas être modifié.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        """Interdit la suppression physique d’un événement de sécurité."""
        raise ValidationError("Un événement de sécurité ne peut pas être supprimé.")
