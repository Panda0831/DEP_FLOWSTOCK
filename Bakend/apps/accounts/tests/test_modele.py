"""Vérifie les modèles, les contraintes PostgreSQL et le manager."""

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import override_settings

from apps.accounts import urls as routes_comptes
from apps.accounts.admin import JournalSecuriteAdmin
from apps.accounts.models import JournalSecurite, RoleUtilisateur, TypeEvenementSecurite

Utilisateur = get_user_model()


@pytest.mark.django_db
def test_manager_normalise_email_et_hache_le_mot_de_passe():
    utilisateur = Utilisateur.objects.creer_utilisateur(
        email="  VENDEUR@Exemple.test ",
        mot_de_passe="Fleur!Miroir8472",
        nom="Rakoto",
        prenom="Hery",
    )

    assert utilisateur.email == "vendeur@exemple.test"
    assert utilisateur.check_password("Fleur!Miroir8472")
    assert utilisateur.password != "Fleur!Miroir8472"


@pytest.mark.django_db
def test_interfaces_django_du_manager_creent_des_comptes_corrects():
    vendeur = Utilisateur.objects.create_user(
        email="manager-vendeur@exemple.test",
        password="T2!rV8#fJ5@xK3$m",
        nom="Rakoto",
        prenom="Hery",
    )
    administrateur = Utilisateur.objects.create_superuser(
        email="manager-admin@exemple.test",
        password="S4!kM7#bQ2@zL9$p",
        nom="Rakoto",
        prenom="Hery",
        role=RoleUtilisateur.VENDEUR,
    )

    assert vendeur.role == RoleUtilisateur.VENDEUR
    assert administrateur.role == RoleUtilisateur.ADMIN
    assert administrateur.is_superuser


@pytest.mark.django_db
@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.Argon2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
def test_manager_stocke_le_mot_de_passe_en_argon2():
    utilisateur = Utilisateur.objects.creer_utilisateur(
        email="argon2@exemple.test",
        mot_de_passe="Fleur!Miroir8472",
        nom="Rakoto",
        prenom="Hery",
    )

    assert utilisateur.password.startswith("argon2$")


@pytest.mark.django_db
def test_interface_standard_du_manager_refuse_les_mots_de_passe_absents():
    with pytest.raises(ValueError, match="mot de passe est obligatoire"):
        Utilisateur.objects.create_user(
            email="sans-mot-de-passe@exemple.test",
            password=None,
            nom="Rakoto",
            prenom="Hery",
        )

    with pytest.raises(ValueError, match="mot de passe est obligatoire"):
        Utilisateur.objects.create_superuser(
            email="sans-mot-de-passe@exemple.test",
            password=None,
            nom="Rakoto",
            prenom="Hery",
        )


@pytest.mark.django_db
def test_proprietes_et_permissions_du_modele_utilisateur(utilisateur_vendeur):
    assert str(utilisateur_vendeur) == utilisateur_vendeur.email
    assert not utilisateur_vendeur.is_staff
    assert not utilisateur_vendeur.est_administrateur
    assert not utilisateur_vendeur.has_perm("accounts.view_utilisateur")
    assert not utilisateur_vendeur.has_module_perms("accounts")

    administrateur = Utilisateur.objects.creer_superutilisateur(
        email="admin-modele@exemple.test",
        mot_de_passe="R7!mV2#qL9@cB5$z",
        nom="Rakoto",
        prenom="Hery",
    )

    assert administrateur.is_staff
    assert administrateur.est_administrateur
    assert administrateur.has_perm("accounts.view_utilisateur")
    assert administrateur.has_module_perms("accounts")


@pytest.mark.django_db
def test_index_unique_refuse_email_de_casse_differente():
    Utilisateur.objects.creer_utilisateur(
        email="unique@exemple.test",
        mot_de_passe="Fleur!Miroir8472",
        nom="Rakoto",
        prenom="Hery",
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Utilisateur.objects.creer_utilisateur(
            email="UNIQUE@exemple.test",
            mot_de_passe="Fleur!Miroir8472",
            nom="Rakoto",
            prenom="Hery",
        )


@pytest.mark.django_db
def test_contrainte_role_refuse_une_valeur_inconnue():
    utilisateur = Utilisateur(
        email="role@exemple.test",
        nom="Rakoto",
        prenom="Hery",
        role="inconnu",
    )
    utilisateur.set_password("Fleur!Miroir8472")

    with pytest.raises(IntegrityError), transaction.atomic():
        utilisateur.save()


@pytest.mark.django_db
def test_createsuperuser_force_le_role_administrateur(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "Q6!wR2#bZ8@fT4$hK9")

    call_command(
        "createsuperuser",
        email="premier-admin@exemple.test",
        nom="Rakoto",
        prenom="Hery",
        interactive=False,
        verbosity=0,
    )

    utilisateur = Utilisateur.objects.get(email="premier-admin@exemple.test")
    assert utilisateur.role == RoleUtilisateur.ADMIN
    assert utilisateur.is_superuser
    assert utilisateur.is_staff
    assert not utilisateur.doit_changer_mot_de_passe


@pytest.mark.django_db
def test_journal_securite_est_immuable():
    evenement = JournalSecurite.objects.create(
        type_evenement=TypeEvenementSecurite.CONNEXION_REUSSIE,
        succes=True,
        details={"methode": "mot_de_passe"},
    )

    evenement.succes = False
    assert "connexion_reussie" in str(evenement)
    with pytest.raises(ValidationError, match="ne peut pas être modifié"):
        evenement.save()
    with pytest.raises(ValidationError, match="ne peut pas être supprimé"):
        evenement.delete()


@pytest.mark.django_db
def test_champs_sql_du_modele_utilisateur_sont_en_francais():
    colonnes = {
        champ.name: champ.db_column or champ.name for champ in Utilisateur._meta.concrete_fields
    }

    assert colonnes["password"] == "mot_de_passe"
    assert colonnes["last_login"] == "derniere_connexion"
    assert colonnes["is_superuser"] == "est_super_utilisateur"
    assert Utilisateur._meta.db_table == "utilisateurs"


def test_journal_admin_est_strictement_en_lecture_seule():
    administration = JournalSecuriteAdmin(JournalSecurite, admin.site)

    assert not administration.has_add_permission(None)
    assert not administration.has_change_permission(None)
    assert not administration.has_delete_permission(None)


def test_route_connexion_est_initialisee():
    assert routes_comptes.app_name == "accounts"
    assert len(routes_comptes.urlpatterns) == 12
    assert routes_comptes.urlpatterns[0].name == "connexion"
    assert routes_comptes.urlpatterns[1].name == "rafraichissement_jetons"
    assert routes_comptes.urlpatterns[2].name == "mon_profil"
    assert routes_comptes.urlpatterns[3].name == "changer_mot_de_passe"
    assert routes_comptes.urlpatterns[4].name == "demander_reinitialisation_mot_de_passe"
    assert routes_comptes.urlpatterns[5].name == "confirmer_reinitialisation_mot_de_passe"
    assert routes_comptes.urlpatterns[6].name == "deconnexion"
    assert routes_comptes.urlpatterns[7].name == "creer_utilisateur"
    assert routes_comptes.urlpatterns[8].name == "detail_utilisateur"
    assert routes_comptes.urlpatterns[9].name == "desactiver_utilisateur"
    assert routes_comptes.urlpatterns[10].name == "uuid_utilisateur_invalide"
    assert routes_comptes.urlpatterns[11].name == "uuid_desactivation_invalide"
