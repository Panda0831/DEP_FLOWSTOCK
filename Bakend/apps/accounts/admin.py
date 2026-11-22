"""Administration Django des comptes et du journal."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import JournalSecurite, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """Affiche les comptes sans exposer de secrets ni gérer les rôles API."""

    model = Utilisateur
    ordering = ("email",)
    list_display = ("email", "nom", "prenom", "role", "is_active", "is_superuser")
    list_filter = ("role", "is_active", "is_superuser")
    search_fields = ("email", "nom", "prenom")
    filter_horizontal = ()
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identité", {"fields": ("nom", "prenom", "telephone", "role")}),
        (
            "État",
            {
                "fields": (
                    "is_active",
                    "is_superuser",
                    "doit_changer_mot_de_passe",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "last_login",
                    "date_dernier_changement_mot_de_passe",
                    "date_creation",
                    "date_modification",
                )
            },
        ),
    )
    readonly_fields = (
        "last_login",
        "date_dernier_changement_mot_de_passe",
        "date_creation",
        "date_modification",
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nom", "prenom", "password1", "password2"),
            },
        ),
    )


@admin.register(JournalSecurite)
class JournalSecuriteAdmin(admin.ModelAdmin):
    """Expose le journal en lecture seule."""

    list_display = ("date_evenement", "type_evenement", "succes", "acteur", "utilisateur_cible")
    list_filter = ("type_evenement", "succes")
    search_fields = ("email_saisi", "route")
    readonly_fields = tuple(
        champ.name for champ in JournalSecurite._meta.get_fields() if champ.concrete
    )

    def has_add_permission(self, requete) -> bool:
        """Interdit l’ajout manuel d’un événement."""
        return False

    def has_change_permission(self, requete, obj=None) -> bool:
        """Interdit la modification d’un événement."""
        return False

    def has_delete_permission(self, requete, obj=None) -> bool:
        """Interdit la suppression d’un événement."""
        return False
