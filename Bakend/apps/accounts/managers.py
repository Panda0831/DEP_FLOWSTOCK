"""Gestion sécurisée de la création des comptes utilisateurs."""

from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.password_validation import validate_password


class UtilisateurManager(BaseUserManager):
    """Crée des utilisateurs avec e-mail normalisé et mot de passe haché."""

    use_in_migrations = True

    def creer_utilisateur(
        self,
        email: str,
        mot_de_passe: str,
        nom: str,
        prenom: str,
        telephone: str = "",
        role: str = "vendeur",
        **champs: Any,
    ):
        """Crée un utilisateur ordinaire après validation du mot de passe."""
        from apps.accounts.models import Utilisateur

        adresse = self.normalize_email(email).strip().lower()
        utilisateur = Utilisateur(
            email=adresse,
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            role=role,
            **champs,
        )
        utilisateur.set_password(mot_de_passe)
        validate_password(mot_de_passe, utilisateur)
        utilisateur.save(using=self._db)
        return utilisateur

    def creer_superutilisateur(
        self,
        email: str,
        mot_de_passe: str,
        nom: str,
        prenom: str,
        **champs: Any,
    ):
        """Crée un super-utilisateur toujours associé au rôle API administrateur."""
        champs.pop("role", None)
        champs["is_superuser"] = True
        champs["is_active"] = True
        champs["doit_changer_mot_de_passe"] = False
        return self.creer_utilisateur(
            email=email,
            mot_de_passe=mot_de_passe,
            nom=nom,
            prenom=prenom,
            role="admin",
            **champs,
        )

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ):
        """Expose le point d’entrée requis par les commandes Django."""
        if password is None:
            raise ValueError("Un mot de passe est obligatoire.")
        return self.creer_utilisateur(
            email=email,
            mot_de_passe=password,
            **extra_fields,
        )

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ):
        """Crée un compte d’administration selon l’interface Django obligatoire."""
        if password is None:
            raise ValueError("Un mot de passe est obligatoire.")
        extra_fields.pop("role", None)
        return self.creer_superutilisateur(
            email=email,
            mot_de_passe=password,
            **extra_fields,
        )
