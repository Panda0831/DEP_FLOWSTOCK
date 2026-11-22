"""Configuration de l’application transverse."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Déclare les composants communs aux applications StockFlow."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
