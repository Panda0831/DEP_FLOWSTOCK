"""Validateurs de sécurité communs."""

from django.core.exceptions import ValidationError


class LongueurMaximaleMotDePasseValidator:
    """Refuse les mots de passe trop longs avant tout hachage coûteux."""

    limite = 128

    def validate(self, password: str, user: object | None = None) -> None:
        """Lève une erreur si le mot de passe dépasse la limite autorisée."""
        if len(password) > self.limite:
            raise ValidationError(
                "Le mot de passe ne peut pas dépasser %(limite)d caractères.",
                code="mot_de_passe_trop_long",
                params={"limite": self.limite},
            )

    def get_help_text(self) -> str:
        """Décrit la longueur maximale acceptée."""
        return f"Le mot de passe ne peut pas dépasser {self.limite} caractères."
