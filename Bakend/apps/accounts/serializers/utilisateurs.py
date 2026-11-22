"""Entrées et sorties JSON de l’administration des utilisateurs."""

import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.constantes import (
    LONGUEUR_MAXIMALE_EMAIL,
    LONGUEUR_MAXIMALE_MOT_DE_PASSE,
    LONGUEUR_MAXIMALE_NOM,
    LONGUEUR_MAXIMALE_TELEPHONE,
)
from apps.accounts.models import RoleUtilisateur, Utilisateur
from apps.core.mixins import RefusChampsInconnusMixin


class ChampTexteStrict(serializers.CharField):
    """Refuse les valeurs JSON qui ne sont pas réellement du texte."""

    def to_internal_value(self, valeur):
        if not isinstance(valeur, str):
            self.fail("invalid")
        return super().to_internal_value(valeur)


class ChampEmailStrict(serializers.EmailField):
    """Valide une adresse e-mail sans convertir les autres types JSON en texte."""

    def to_internal_value(self, valeur):
        if not isinstance(valeur, str):
            self.fail("invalid")
        return super().to_internal_value(valeur)


class UtilisateurCreationSerializer(RefusChampsInconnusMixin, serializers.Serializer):
    """Valide strictement les champs autorisés à la création d’un compte."""

    email = ChampEmailStrict(
        max_length=LONGUEUR_MAXIMALE_EMAIL,
        help_text="Adresse e-mail unique; espaces retirés et casse normalisée.",
    )
    nom = ChampTexteStrict(
        max_length=LONGUEUR_MAXIMALE_NOM,
        help_text="Nom de famille, de 1 à 100 caractères sans caractère de contrôle.",
    )
    prenom = ChampTexteStrict(
        max_length=LONGUEUR_MAXIMALE_NOM,
        help_text="Prénom, de 1 à 100 caractères sans caractère de contrôle.",
    )
    telephone = ChampTexteStrict(
        max_length=LONGUEUR_MAXIMALE_TELEPHONE,
        required=False,
        allow_blank=True,
        help_text="Téléphone optionnel; espaces, tirets et points sont retirés.",
    )
    role = serializers.ChoiceField(
        choices=RoleUtilisateur.choices,
        required=False,
        default=RoleUtilisateur.VENDEUR,
        error_messages={"invalid_choice": "Rôle invalide. Choisissez admin ou vendeur."},
        help_text="Rôle métier; vendeur par défaut.",
    )
    mot_de_passe_initial = ChampTexteStrict(
        max_length=LONGUEUR_MAXIMALE_MOT_DE_PASSE,
        trim_whitespace=False,
        write_only=True,
        help_text="Mot de passe temporaire conforme à la politique de sécurité.",
    )

    def validate_email(self, valeur: str) -> str:
        """Uniformise l’adresse avant la vérification d’unicité."""
        return valeur.strip().lower()

    def validate_nom(self, valeur: str) -> str:
        """Refuse les caractères de contrôle dans le nom."""
        if re.search(r"[\x00-\x1f\x7f]", valeur):
            raise serializers.ValidationError("Les caractères de contrôle sont interdits.")
        return valeur

    def validate_prenom(self, valeur: str) -> str:
        """Refuse les caractères de contrôle dans le prénom."""
        if re.search(r"[\x00-\x1f\x7f]", valeur):
            raise serializers.ValidationError("Les caractères de contrôle sont interdits.")
        return valeur

    def validate_telephone(self, valeur: str) -> str:
        """Normalise puis valide le téléphone selon le format documenté."""
        telephone = re.sub(r"[\s.-]", "", valeur)
        if telephone and re.fullmatch(r"\+?[0-9]{8,15}", telephone) is None:
            raise serializers.ValidationError("Saisissez un numéro de téléphone valide.")
        return telephone

    def validate(self, donnees):
        """Valide le mot de passe sans le modifier ni le nettoyer."""
        utilisateur = Utilisateur(
            email=donnees["email"],
            nom=donnees["nom"],
            prenom=donnees["prenom"],
        )
        try:
            validate_password(donnees["mot_de_passe_initial"], utilisateur)
        except DjangoValidationError as erreur:
            raise serializers.ValidationError(
                {"mot_de_passe_initial": erreur.messages},
            ) from erreur
        return donnees


class UtilisateurAdminSerializer(serializers.Serializer):
    """Liste blanche des champs renvoyés aux administrateurs."""

    uuid = serializers.UUIDField(help_text="Identifiant public unique du compte.")
    email = serializers.EmailField(help_text="Adresse e-mail normalisée.")
    nom = serializers.CharField(help_text="Nom de famille.")
    prenom = serializers.CharField(help_text="Prénom.")
    telephone = serializers.CharField(help_text="Téléphone; chaîne vide si non renseigné.")
    role = serializers.ChoiceField(
        choices=RoleUtilisateur.choices,
        help_text="Rôle métier du compte.",
    )
    est_actif = serializers.BooleanField(
        source="is_active",
        help_text="Indique si le compte peut s’authentifier.",
    )
    doit_changer_mot_de_passe = serializers.BooleanField(
        help_text="Indique si le compte doit changer son mot de passe.",
    )
    date_creation = serializers.DateTimeField(help_text="Date de création avec fuseau horaire.")
    derniere_connexion = serializers.DateTimeField(
        source="last_login",
        allow_null=True,
        help_text="Dernière connexion; null si le compte ne s’est jamais connecté.",
    )
    date_dernier_changement_mot_de_passe = serializers.DateTimeField(
        allow_null=True,
        help_text="Dernier changement du mot de passe; null si absent.",
    )
    date_modification = serializers.DateTimeField(help_text="Dernière modification avec fuseau.")


class UtilisateurModificationSerializer(RefusChampsInconnusMixin, serializers.Serializer):
    """Liste blanche des champs modifiables par un administrateur."""

    email = ChampEmailStrict(
        required=False,
        max_length=LONGUEUR_MAXIMALE_EMAIL,
        help_text="Adresse e-mail unique, normalisée en minuscules.",
    )
    nom = ChampTexteStrict(
        required=False,
        max_length=LONGUEUR_MAXIMALE_NOM,
        help_text="Nom de famille.",
    )
    prenom = ChampTexteStrict(
        required=False,
        max_length=LONGUEUR_MAXIMALE_NOM,
        help_text="Prénom.",
    )
    telephone = ChampTexteStrict(
        required=False,
        allow_blank=True,
        max_length=LONGUEUR_MAXIMALE_TELEPHONE,
        help_text="Téléphone optionnel; espaces, tirets et points sont retirés.",
    )
    role = serializers.ChoiceField(
        choices=RoleUtilisateur.choices,
        required=False,
        error_messages={"invalid_choice": "Rôle invalide. Choisissez admin ou vendeur."},
        help_text="Rôle métier admin ou vendeur.",
    )

    def validate_email(self, valeur: str) -> str:
        """Uniformise l’adresse avant la vérification d’unicité."""
        return valeur.strip().lower()

    def validate_nom(self, valeur: str) -> str:
        """Refuse les caractères de contrôle dans le nom."""
        if re.search(r"[\x00-\x1f\x7f]", valeur):
            raise serializers.ValidationError("Les caractères de contrôle sont interdits.")
        return valeur

    def validate_prenom(self, valeur: str) -> str:
        """Refuse les caractères de contrôle dans le prénom."""
        if re.search(r"[\x00-\x1f\x7f]", valeur):
            raise serializers.ValidationError("Les caractères de contrôle sont interdits.")
        return valeur

    def validate_telephone(self, valeur: str) -> str:
        """Normalise puis valide le téléphone selon le format documenté."""
        telephone = re.sub(r"[\s.-]", "", valeur)
        if telephone and re.fullmatch(r"\+?[0-9]{8,15}", telephone) is None:
            raise serializers.ValidationError("Saisissez un numéro de téléphone valide.")
        return telephone


class FiltresListeUtilisateursSerializer(serializers.Serializer):
    """Valide les filtres et le tri autorisés pour la liste administrateur."""

    search = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        help_text="Recherche partielle dans le nom, le prénom et l’e-mail.",
    )
    role = serializers.ChoiceField(
        choices=RoleUtilisateur.choices,
        required=False,
        help_text="Filtre par rôle admin ou vendeur.",
    )
    active = serializers.ChoiceField(
        choices=(("true", "Actif"), ("false", "Inactif")),
        required=False,
        help_text="Filtre par état actif, valeur true ou false.",
    )
    ordering = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Tri autorisé : nom, prenom, email, role ou date_creation; préfixe - inversant.",
    )

    def validate_ordering(self, valeur: str) -> list[str]:
        """Refuse les tris hors liste blanche et normalise chaque direction."""
        champs_autorises = {"nom", "prenom", "email", "role", "date_creation"}
        champs = valeur.split(",")
        if not champs or any(
            not champ or champ.lstrip("-") not in champs_autorises or champ.count("-") > 1
            for champ in champs
        ):
            raise serializers.ValidationError(
                "Tri invalide. Champs autorisés : nom, prenom, email, role, date_creation."
            )
        return champs


class ReponseListeUtilisateursSerializer(serializers.Serializer):
    """Format paginé standard de la liste des utilisateurs."""

    count = serializers.IntegerField(help_text="Nombre total de comptes correspondant aux filtres.")
    next = serializers.URLField(
        allow_null=True,
        help_text="URL de la page suivante ou null.",
    )
    previous = serializers.URLField(
        allow_null=True,
        help_text="URL de la page précédente ou null.",
    )
    results = UtilisateurAdminSerializer(
        many=True,
        help_text="Comptes de la page courante, sans données sensibles.",
    )
