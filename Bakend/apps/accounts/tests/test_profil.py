"""Vérifie la consultation sécurisée du profil authentifié."""

import pytest
from django.core.cache import cache
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

ROUTE_PROFIL = "/api/v1/auth/me/"
CHAMPS_PROFIL = {
    "uuid",
    "email",
    "nom",
    "prenom",
    "telephone",
    "role",
    "doit_changer_mot_de_passe",
    "date_creation",
    "derniere_connexion",
}


@pytest.fixture(autouse=True)
def vider_cache_profil():
    cache.clear()


def publier_profil(jeton: str | None = None):
    client = APIClient()
    if jeton is not None:
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
    return client.get(ROUTE_PROFIL)


@pytest.mark.django_db
def test_vendeur_peut_consulter_exactement_son_profil(utilisateur_vendeur):
    jeton = str(AccessToken.for_user(utilisateur_vendeur))

    reponse = publier_profil(jeton)

    assert reponse.status_code == 200
    assert set(reponse.data) == CHAMPS_PROFIL
    assert reponse.data == {
        "uuid": str(utilisateur_vendeur.uuid),
        "email": utilisateur_vendeur.email,
        "nom": utilisateur_vendeur.nom,
        "prenom": utilisateur_vendeur.prenom,
        "telephone": utilisateur_vendeur.telephone,
        "role": utilisateur_vendeur.role,
        "doit_changer_mot_de_passe": False,
        "date_creation": timezone.localtime(utilisateur_vendeur.date_creation).isoformat(),
        "derniere_connexion": None,
    }
    assert not {"id", "password", "is_superuser", "est_actif"} & set(reponse.data)
    assert reponse["Cache-Control"] == "no-store"
    assert reponse["Pragma"] == "no-cache"


@pytest.mark.django_db
def test_administrateur_peut_consulter_son_profil(utilisateur_vendeur):
    utilisateur_vendeur.role = "admin"
    utilisateur_vendeur.is_superuser = True
    utilisateur_vendeur.save(update_fields=["role", "is_superuser"])
    jeton = str(AccessToken.for_user(utilisateur_vendeur))

    reponse = publier_profil(jeton)

    assert reponse.status_code == 200
    assert reponse.data["role"] == "admin"


@pytest.mark.django_db
def test_consultation_est_autorisee_avec_changement_de_mot_de_passe_requis(
    utilisateur_vendeur,
):
    utilisateur_vendeur.doit_changer_mot_de_passe = True
    utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])
    jeton = str(AccessToken.for_user(utilisateur_vendeur))

    reponse = publier_profil(jeton)

    assert reponse.status_code == 200
    assert reponse.data["doit_changer_mot_de_passe"] is True


@pytest.mark.django_db
def test_utilisateur_anonyme_recoit_401_non_authentifie():
    reponse = publier_profil()

    assert reponse.status_code == 401
    assert reponse.data == {
        "detail": "Authentification requise.",
        "code": "non_authentifie",
    }
    assert reponse["WWW-Authenticate"].startswith("Bearer")
    assert reponse["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_jeton_access_expire_recoit_401_jeton_expire(utilisateur_vendeur):
    with freeze_time("2026-01-01T00:00:00Z"):
        jeton = str(AccessToken.for_user(utilisateur_vendeur))

    with freeze_time("2026-01-01T00:16:00Z"):
        reponse = publier_profil(jeton)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "jeton_expire"


@pytest.mark.django_db
def test_jeton_access_falsifie_recoit_401_jeton_invalide(utilisateur_vendeur):
    jeton = str(AccessToken.for_user(utilisateur_vendeur))
    jeton_falsifie = f"{jeton[:-1]}{'A' if jeton[-1] != 'A' else 'B'}"

    reponse = publier_profil(jeton_falsifie)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "jeton_invalide", reponse.data


@pytest.mark.django_db
def test_compte_desactive_ne_peut_pas_consulter_son_profil(utilisateur_vendeur):
    jeton = str(AccessToken.for_user(utilisateur_vendeur))
    utilisateur_vendeur.is_active = False
    utilisateur_vendeur.save(update_fields=["is_active"])

    reponse = publier_profil(jeton)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "jeton_invalide", reponse.data


def test_swagger_documente_tous_les_resultats_du_profil():
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/auth/me/"]["get"]

    assert set(operation["responses"]) == {"200", "401", "405", "429", "500"}
    assert operation.get("security")
    assert set(operation["responses"]["401"]["content"]["application/json"]["examples"]) == {
        "NonAuthentifie",
        "JetonExpire",
        "JetonInvalide",
    }
    assert set(operation["responses"]["405"]["content"]["application/json"]["examples"]) == {
        "MethodeInterdite",
    }

    modification = schema["paths"]["/api/v1/auth/me/"]["patch"]
    assert set(modification["responses"]) == {
        "200",
        "400",
        "401",
        "403",
        "405",
        "415",
        "429",
        "500",
    }
    assert modification.get("security")
    assert set(modification["responses"]["400"]["content"]["application/json"]["examples"]) == {
        "Validation",
        "ChampsInconnus",
        "JsonMalforme",
    }
    assert set(modification["responses"]["403"]["content"]["application/json"]["examples"]) == {
        "ChangementMotDePasseRequis",
    }
