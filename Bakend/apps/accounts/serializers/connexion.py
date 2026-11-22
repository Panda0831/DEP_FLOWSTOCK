"""Entrées et sorties JSON de l’authentification."""

from rest_framework import serializers

from apps.accounts.models import RoleUtilisateur
from apps.core.mixins import RefusChampsInconnusMixin


class ConnexionSerializer(RefusChampsInconnusMixin, serializers.Serializer):
    """Valide les identifiants sans modifier le mot de passe reçu."""

    email = serializers.EmailField(
        max_length=254,
        help_text="Adresse e-mail de connexion; espaces externes retirés et casse normalisée.",
    )
    mot_de_passe = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
        help_text="Mot de passe non vide, conservé exactement comme saisi.",
    )

    def validate_email(self, valeur: str) -> str:
        """Uniformise l’adresse avant la recherche et la limitation par e-mail."""
        return valeur.strip().lower()


class UtilisateurResumeConnexionSerializer(serializers.Serializer):
    """Champs de compte autorisés dans une réponse de connexion."""

    uuid = serializers.UUIDField(help_text="Identifiant public unique du compte.")
    email = serializers.EmailField(help_text="Adresse e-mail normalisée du compte.")
    nom = serializers.CharField(help_text="Nom de famille du titulaire.")
    prenom = serializers.CharField(help_text="Prénom du titulaire.")
    role = serializers.ChoiceField(
        choices=RoleUtilisateur.choices,
        help_text="Rôle métier du compte.",
    )
    doit_changer_mot_de_passe = serializers.BooleanField(
        help_text="Indique si un changement de mot de passe est exigé.",
    )


class ReponseConnexionSerializer(serializers.Serializer):
    """Réponse JSON émise après une authentification réussie."""

    access = serializers.CharField(help_text="Jeton JWT d’accès.")
    refresh = serializers.CharField(help_text="Jeton JWT de rafraîchissement.")
    utilisateur = UtilisateurResumeConnexionSerializer(
        help_text="Résumé public du compte authentifié.",
    )


class ErreurSerializer(serializers.Serializer):
    """Format JSON standard des erreurs sans détails de validation."""

    detail = serializers.CharField(help_text="Message d’erreur lisible en français.")
    code = serializers.CharField(help_text="Code machine stable de l’erreur.")


class ErreurValidationSerializer(ErreurSerializer):
    """Format JSON des erreurs de validation et de parsing."""

    erreurs = serializers.DictField(
        child=serializers.JSONField(),
        help_text="Erreurs indexées par champ; vide si le JSON ou son type est invalide.",
    )


class ErreurOuValidationSerializer(ErreurSerializer):
    """Documente les réponses d’erreur métier ou de validation sous un même code HTTP."""

    erreurs = serializers.DictField(
        child=serializers.JSONField(),
        required=False,
        help_text="Erreurs indexées par champ, présente uniquement lors d’une validation.",
    )
