"""Entrées et sorties JSON du renouvellement des jetons."""

from rest_framework import serializers

from apps.core.mixins import RefusChampsInconnusMixin


class ChampJetonRefresh(serializers.CharField):
    """Refuse toute représentation non textuelle du jeton."""

    def to_internal_value(self, valeur):
        if not isinstance(valeur, str):
            self.fail("invalid")
        return super().to_internal_value(valeur)


class RafraichissementSerializer(RefusChampsInconnusMixin, serializers.Serializer):
    """Valide le jeton reçu sans accepter d’autres champs."""

    refresh = ChampJetonRefresh(
        max_length=8192,
        trim_whitespace=True,
        write_only=True,
        help_text="Jeton JWT de rafraîchissement encore valide.",
    )


class DeconnexionSerializer(RefusChampsInconnusMixin, serializers.Serializer):
    """Valide le jeton à révoquer sans accepter d’autres champs."""

    refresh = ChampJetonRefresh(
        max_length=8192,
        trim_whitespace=True,
        write_only=True,
        help_text="Jeton JWT de rafraîchissement à révoquer.",
    )


class ReponseRafraichissementSerializer(serializers.Serializer):
    """Paire de jetons retournée après une rotation réussie."""

    access = serializers.CharField(help_text="Nouveau jeton JWT d’accès.")
    refresh = serializers.CharField(help_text="Nouveau jeton JWT de rafraîchissement.")
