"""Sorties JSON du profil utilisateur."""

import re

from rest_framework import serializers

from apps.accounts.constantes import LONGUEUR_MAXIMALE_NOM, LONGUEUR_MAXIMALE_TELEPHONE
from apps.accounts.models import RoleUtilisateur
from apps.accounts.serializers.utilisateurs import ChampTexteStrict
from apps.core.mixins import RefusChampsInconnusMixin


class ProfilSerializer(serializers.Serializer):
    """Liste blanche des informations visibles par le titulaire du compte."""

    uuid = serializers.UUIDField(help_text="Identifiant public unique du compte.")
    email = serializers.EmailField(help_text="Adresse e-mail normalisée du titulaire.")
    nom = serializers.CharField(help_text="Nom de famille du titulaire.")
    prenom = serializers.CharField(help_text="Prénom du titulaire.")
    telephone = serializers.CharField(help_text="Téléphone du titulaire, vide si non renseigné.")
    role = serializers.ChoiceField(
        choices=RoleUtilisateur.choices,
        help_text="Rôle métier actuel du titulaire.",
    )
    doit_changer_mot_de_passe = serializers.BooleanField(
        help_text="Indique si un changement de mot de passe est exigé.",
    )
    date_creation = serializers.DateTimeField(help_text="Date de création, au format ISO 8601.")
    derniere_connexion = serializers.DateTimeField(
        source="last_login",
        allow_null=True,
        help_text="Dernière connexion au format ISO 8601, nulle si aucune.",
    )


class ProfilModificationSerializer(RefusChampsInconnusMixin, serializers.Serializer):
    """Liste blanche des champs modifiables par le titulaire."""

    nom = ChampTexteStrict(required=False, max_length=LONGUEUR_MAXIMALE_NOM)
    prenom = ChampTexteStrict(required=False, max_length=LONGUEUR_MAXIMALE_NOM)
    telephone = ChampTexteStrict(
        required=False,
        allow_blank=True,
        max_length=LONGUEUR_MAXIMALE_TELEPHONE,
    )

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
