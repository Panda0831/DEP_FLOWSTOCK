"""Permissions métier du module comptes."""

from rest_framework.permissions import BasePermission

from apps.accounts.models import RoleUtilisateur


class EstAdministrateur(BasePermission):
    """Autorise uniquement un administrateur actif."""

    message = "Cette action est réservée aux administrateurs."
    code = "acces_interdit"

    def has_permission(self, requete, vue) -> bool:
        """Vérifie le statut actif et relit le rôle métier en base."""
        utilisateur = requete.user
        return bool(
            utilisateur
            and utilisateur.is_authenticated
            and utilisateur.is_active
            and utilisateur.role == RoleUtilisateur.ADMIN
        )


class EstVendeur(BasePermission):
    """Permission réutilisable par les futurs modules, sans route associée ici."""

    message = "Cette action est réservée aux vendeurs."
    code = "acces_interdit"

    def has_permission(self, requete, vue) -> bool:
        """Vérifie que le compte authentifié possède le rôle vendeur."""
        utilisateur = requete.user
        return bool(
            utilisateur
            and utilisateur.is_authenticated
            and utilisateur.is_active
            and utilisateur.role == RoleUtilisateur.VENDEUR
        )


class ChangementMotDePasseNonRequis(BasePermission):
    """Bloque les comptes qui doivent définir un nouveau mot de passe."""

    message = "Un changement de mot de passe est requis."
    code = "changement_mot_de_passe_requis"

    def has_permission(self, requete, vue) -> bool:
        """Autorise uniquement les opérations nécessaires au changement forcé."""
        utilisateur = requete.user
        if not utilisateur or not utilisateur.is_authenticated:
            return True

        if not utilisateur.doit_changer_mot_de_passe:
            return True

        return bool(
            getattr(vue, "autoriser_mot_de_passe_initial", False)
            or (requete.method == "GET" and requete.path.endswith("/auth/me/"))
            or (
                requete.method == "POST"
                and (
                    requete.path.endswith("/auth/logout/")
                    or requete.path.endswith("/auth/password/change/")
                )
            )
        )
