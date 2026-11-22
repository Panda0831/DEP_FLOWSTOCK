"""Configuration du module comptes."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Déclare les modèles du module utilisateurs."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Comptes utilisateurs"
