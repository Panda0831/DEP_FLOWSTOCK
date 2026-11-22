"""Entrées JSON pour le changement et la réinitialisation de mot de passe."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.constantes import LONGUEUR_MAXIMALE_EMAIL, LONGUEUR_MAXIMALE_MOT_DE_PASSE
from apps.accounts.serializers.utilisateurs import ChampEmailStrict, ChampTexteStrict
from apps.core.mixins import RefusChampsInconnusMixin


class ChangementMotDePasseSerializer(RefusChampsInconnusMixin, serializers.Serializer):
    """Valide le changement demandé par le titulaire authentifié."""

    ancien_mot_de_passe = ChampTexteStrict(
        max_length=LONGUEUR_MAXIMALE_MOT_DE_PASSE,
        trim_whitespace=False,
        write_only=True,
        help_text="Mot de passe actuel, transmis sans modification.",
    )
    nouveau_mot_de_passe = ChampTexteStrict(
        max_length=LONGUEUR_MAXIMALE_MOT_DE_PASSE,
        trim_whitespace=False,
        write_only=True,
        help_text="Nouveau mot de passe conforme aux validateurs configurés.",
    )
    confirmation_nouveau_mot_de_passe = ChampTexteStrict(
        max_length=LONGUEUR_MAXIMALE_MOT_DE_PASSE,
        trim_whitespace=False,
        write_only=True,
        help_text="Répétition exacte du nouveau mot de passe.",
    )

    def validate(self, donnees):
        """Vérifie la confirmation et les validateurs Django du mot de passe."""
        if donnees["nouveau_mot_de_passe"] != donnees["confirmation_nouveau_mot_de_passe"]:
            raise serializers.ValidationError(
                {
                    "confirmation_nouveau_mot_de_passe": [
                        "La confirmation du mot de passe ne correspond pas."
                    ]
                }
            )
        if donnees["nouveau_mot_de_passe"] == donnees["ancien_mot_de_passe"]:
            raise serializers.ValidationError(
                {
                    "nouveau_mot_de_passe": [
                        "Le nouveau mot de passe doit être différent de l’ancien."
                    ]
                }
            )

        try:
            validate_password(
                donnees["nouveau_mot_de_passe"],
                self.context["request"].user,
            )
        except DjangoValidationError as erreur:
            raise serializers.ValidationError(
                {"nouveau_mot_de_passe": erreur.messages},
            ) from erreur
        return donnees


class DemandeReinitialisationSerializer(RefusChampsInconnusMixin, serializers.Serializer):
    """Valide l’adresse utilisée pour demander un lien de réinitialisation."""

    email = ChampEmailStrict(
        max_length=LONGUEUR_MAXIMALE_EMAIL,
        help_text="Adresse du compte à réinitialiser; la réponse reste identique.",
    )

    def validate_email(self, valeur: str) -> str:
        """Normalise l’adresse sans la journaliser en clair dans les clés de limite."""
        return valeur.strip().lower()


class ConfirmationReinitialisationSerializer(
    RefusChampsInconnusMixin,
    serializers.Serializer,
):
    """Valide les champs de confirmation sans révéler l’état du jeton."""

    uid = serializers.UUIDField(help_text="UUID du compte transmis dans le lien.")
    token = serializers.CharField(
        max_length=256,
        trim_whitespace=False,
        write_only=True,
        help_text="Jeton à usage unique contenu dans le lien.",
    )
    nouveau_mot_de_passe = ChampTexteStrict(
        max_length=LONGUEUR_MAXIMALE_MOT_DE_PASSE,
        trim_whitespace=False,
        write_only=True,
        help_text="Nouveau mot de passe conforme aux validateurs configurés.",
    )
    confirmation_nouveau_mot_de_passe = ChampTexteStrict(
        max_length=LONGUEUR_MAXIMALE_MOT_DE_PASSE,
        trim_whitespace=False,
        write_only=True,
        help_text="Répétition exacte du nouveau mot de passe.",
    )
