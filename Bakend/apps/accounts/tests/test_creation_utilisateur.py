"""Vérifie la création administrative sécurisée des comptes."""

import pytest
from django.core.cache import cache
from django.db import IntegrityError
from django.test import RequestFactory, override_settings
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import JournalSecurite, TypeEvenementSecurite, Utilisateur
from apps.accounts.services import creer_utilisateur_par_administrateur
from apps.conftest import UtilisateurFabrique

ROUTE_CREATION_UTILISATEUR = "/api/v1/users/"
MOT_DE_PASSE_INITIAL = "Fleur!Miroir8472"
CHAMPS_UTILISATEUR_ADMIN = {
    "uuid",
    "email",
    "nom",
    "prenom",
    "telephone",
    "role",
    "est_actif",
    "doit_changer_mot_de_passe",
    "date_creation",
    "derniere_connexion",
    "date_dernier_changement_mot_de_passe",
    "date_modification",
}


@pytest.fixture(autouse=True)
def vider_cache_creation_utilisateur():
    cache.clear()


def client_administrateur(utilisateur_vendeur):
    utilisateur_vendeur.role = "admin"
    utilisateur_vendeur.is_superuser = True
    utilisateur_vendeur.save(update_fields=["role", "is_superuser"])
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
    )
    return client


def payload_utilisateur(**valeurs):
    return {
        "email": "nouveau@exemple.com",
        "nom": "Andry",
        "prenom": "Miora",
        "telephone": "+261320000000",
        "mot_de_passe_initial": MOT_DE_PASSE_INITIAL,
        **valeurs,
    }


@pytest.mark.django_db
@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.Argon2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
def test_administrateur_cree_un_vendeur_avec_mot_de_passe_hache_et_changement_requis(
    utilisateur_vendeur,
):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(telephone=" +261 32.000-00-00 "),
        format="json",
    )

    assert reponse.status_code == 201
    assert set(reponse.data) == CHAMPS_UTILISATEUR_ADMIN
    assert reponse.data["email"] == "nouveau@exemple.com"
    assert reponse.data["telephone"] == "+261320000000"
    assert reponse.data["role"] == "vendeur"
    assert reponse.data["est_actif"] is True
    assert reponse.data["doit_changer_mot_de_passe"] is True
    assert reponse.data["derniere_connexion"] is None
    assert reponse.data["date_dernier_changement_mot_de_passe"] is None
    assert "password" not in reponse.data

    utilisateur = Utilisateur.objects.get(email="nouveau@exemple.com")
    assert utilisateur.check_password(MOT_DE_PASSE_INITIAL)
    assert utilisateur.password.startswith("argon2$")
    assert utilisateur.doit_changer_mot_de_passe is True
    assert utilisateur.role == "vendeur"
    connexion = APIClient().post(
        "/api/v1/auth/login/",
        {"email": utilisateur.email, "mot_de_passe": MOT_DE_PASSE_INITIAL},
        format="json",
    )
    assert connexion.status_code == 200
    assert connexion.data["utilisateur"]["doit_changer_mot_de_passe"] is True

    client_nouvel_utilisateur = APIClient()
    client_nouvel_utilisateur.credentials(
        HTTP_AUTHORIZATION=f"Bearer {connexion.data['access']}",
    )
    action_protegee = client_nouvel_utilisateur.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(email="autre@exemple.com"),
        format="json",
    )
    assert action_protegee.status_code == 403
    assert action_protegee.data["code"] == "changement_mot_de_passe_requis"

    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.UTILISATEUR_CREE,
    )
    assert evenement.acteur == utilisateur_vendeur
    assert evenement.utilisateur_cible == utilisateur
    assert evenement.succes is True
    assert evenement.details == {"role": "vendeur"}
    assert MOT_DE_PASSE_INITIAL not in str(evenement.details)
    assert reponse["Cache-Control"] == "no-store"
    assert reponse["Pragma"] == "no-cache"


@pytest.mark.django_db
def test_administrateur_peut_creer_un_autre_administrateur(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(role="admin", telephone=""),
        format="json",
    )

    assert reponse.status_code == 201
    assert reponse.data["role"] == "admin"
    assert reponse.data["doit_changer_mot_de_passe"] is True
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.UTILISATEUR_CREE,
    )
    assert evenement.details == {"role": "admin"}


@pytest.mark.django_db
def test_vendeur_ne_peut_pas_creer_un_utilisateur():
    vendeur = UtilisateurFabrique()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(vendeur)}")

    reponse = client.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(),
        format="json",
    )

    assert reponse.status_code == 403
    assert reponse.data["code"] == "acces_interdit"
    evenement = JournalSecurite.objects.get(type_evenement=TypeEvenementSecurite.ACCES_REFUSE)
    assert evenement.details == {"raison": "acces_interdit"}
    assert evenement.succes is False


@pytest.mark.django_db
def test_administrateur_qui_doit_changer_son_mot_de_passe_est_bloque(utilisateur_vendeur):
    utilisateur_vendeur.role = "admin"
    utilisateur_vendeur.doit_changer_mot_de_passe = True
    utilisateur_vendeur.save(update_fields=["role", "doit_changer_mot_de_passe"])
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
    )

    reponse = client.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(),
        format="json",
    )

    assert reponse.status_code == 403
    assert reponse.data["code"] == "changement_mot_de_passe_requis"
    evenement = JournalSecurite.objects.get(type_evenement=TypeEvenementSecurite.ACCES_REFUSE)
    assert evenement.details == {"raison": "changement_mot_de_passe_requis"}


@pytest.mark.django_db
def test_anonyme_ne_peut_pas_creer_un_utilisateur():
    reponse = APIClient().post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(),
        format="json",
    )

    assert reponse.status_code == 401
    assert reponse.data["code"] == "non_authentifie"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("payload", "champ"),
    [
        ({"email": "adresse-invalide"}, "email"),
        ({"email": 12}, "email"),
        ({"mot_de_passe_initial": "court"}, "mot_de_passe_initial"),
        ({"role": "superadmin"}, "role"),
        ({"telephone": "abc"}, "telephone"),
        ({"nom": "Nom\ninterdit"}, "nom"),
        ({"prenom": 12}, "prenom"),
        ({"prenom": "Prenom\ninterdit"}, "prenom"),
        ({"mot_de_passe_initial": "x" * 129}, "mot_de_passe_initial"),
    ],
)
def test_donnees_invalides_sont_refusees(utilisateur_vendeur, payload, champ):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(**payload),
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"
    assert champ in reponse.data["erreurs"]


@pytest.mark.django_db
@pytest.mark.parametrize("champ", ["is_superuser", "est_actif", "uuid", "id"])
def test_champs_sensibles_inconnus_sont_refuses(utilisateur_vendeur, champ):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(**{champ: True}),
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "champs_inconnus"
    assert not Utilisateur.objects.filter(email="nouveau@exemple.com").exists()


@pytest.mark.django_db
def test_email_deja_utilise_avec_une_autre_casse_est_refuse(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    UtilisateurFabrique(email="nouveau@exemple.com")

    reponse = client.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(email="NOUVEAU@EXEMPLE.COM"),
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"
    assert "email" in reponse.data["erreurs"]


@pytest.mark.django_db
def test_mot_de_passe_n_est_jamais_journalise_ni_renvoye(utilisateur_vendeur, caplog):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(),
        format="json",
    )

    assert reponse.status_code == 201
    assert MOT_DE_PASSE_INITIAL not in reponse.content.decode()
    assert MOT_DE_PASSE_INITIAL not in caplog.text
    assert MOT_DE_PASSE_INITIAL not in str(
        JournalSecurite.objects.get(
            type_evenement=TypeEvenementSecurite.UTILISATEUR_CREE,
        ).details
    )


@pytest.mark.django_db
def test_service_refuse_un_mot_de_passe_invalide_sans_hacher_ni_creer(
    utilisateur_vendeur,
):
    donnees = {
        "email": "nouveau@exemple.com",
        "nom": "Andry",
        "prenom": "Miora",
        "telephone": "",
        "role": "vendeur",
        "mot_de_passe_initial": "court",
    }

    with pytest.raises(DRFValidationError, match="mot_de_passe_initial"):
        creer_utilisateur_par_administrateur(
            donnees,
            utilisateur_vendeur,
            RequestFactory().post(ROUTE_CREATION_UTILISATEUR),
        )

    assert not Utilisateur.objects.filter(email=donnees["email"]).exists()


@pytest.mark.django_db
def test_conflit_de_contrainte_email_est_converti_en_409(
    utilisateur_vendeur,
    monkeypatch,
):
    from types import SimpleNamespace

    def simuler_course(**kwargs):
        cause = RuntimeError("contrainte d’unicité simulée")
        cause.diag = SimpleNamespace(constraint_name="uniq_utilisateurs_email_minuscule")
        raise IntegrityError("conflit d’unicité") from cause

    monkeypatch.setattr(Utilisateur.objects, "creer_utilisateur", simuler_course)
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.post(
        ROUTE_CREATION_UTILISATEUR,
        payload_utilisateur(),
        format="json",
    )

    assert reponse.status_code == 409
    assert reponse.data["code"] == "email_deja_utilise"
