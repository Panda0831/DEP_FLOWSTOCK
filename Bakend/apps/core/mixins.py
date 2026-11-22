"""Comportements réutilisables pour les entrées de l’API."""

from collections.abc import Mapping

from rest_framework import serializers


class RefusChampsInconnusMixin:
    """Refuse explicitement les champs absents de la liste blanche du serializer."""

    def to_internal_value(self, donnees: Mapping[str, object]) -> dict[str, object]:
        """Valide la liste des clés reçues avant le traitement DRF standard."""
        if isinstance(donnees, Mapping):
            champs_inconnus = sorted(set(donnees) - set(self.fields))
            if champs_inconnus:
                raise serializers.ValidationError(
                    {"champs_inconnus": ["Champs non autorisés : " + ", ".join(champs_inconnus)]},
                    code="champs_inconnus",
                )

        return super().to_internal_value(donnees)
