"""Vérifie la déconnexion et la révocation des jetons de rafraîchissement."""

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models import JournalSecurite, TypeEvenementSecurite
from apps.conftest import UtilisateurFabrique

ROUTE_DECONNEXION = "/api/v1/auth/logout/"


@pytest.fixture(autouse=True)
def vider_cache_deconnexion():
    cache.clear()


def publier_deconnexion(jeton_acces: str | None, jeton_rafraichissement: str):
    client = APIClient()
    if jeton_acces is not None:
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton_acces}")
    return client.post(
        ROUTE_DECONNEXION,
        {"refresh": jeton_rafraichissement},
        format="json",
    )


@pytest.mark.django_db
def test_deconnexion_revoque_son_jeton_et_est_autorisee_pour_mot_de_passe_initial(
    utilisateur_vendeur,
):
    utilisateur_vendeur.doit_changer_mot_de_passe = True
    utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])
    jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))
    jeton_rafraichissement = str(RefreshToken.for_user(utilisateur_vendeur))

    reponse = publier_deconnexion(jeton_acces, jeton_rafraichissement)

    assert reponse.status_code == 204
    assert reponse.content == b""
    assert reponse["Cache-Control"] == "no-store"
    assert reponse["Pragma"] == "no-cache"
    with pytest.raises(TokenError):
        RefreshToken(jeton_rafraichissement)
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.DECONNEXION,
    )
    assert evenement.acteur == utilisateur_vendeur
    assert evenement.utilisateur_cible == utilisateur_vendeur
    assert jeton_rafraichissement not in str(evenement.details)

    reponse_renouvellement = APIClient().post(
        "/api/v1/auth/token/refresh/",
        {"refresh": jeton_rafraichissement},
        format="json",
    )
    assert reponse_renouvellement.status_code == 401
    assert reponse_renouvellement.data["code"] == "jeton_invalide"


@pytest.mark.django_db
def test_deconnexion_est_idempotente_pour_un_jeton_deja_revoque(utilisateur_vendeur):
    jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))
    jeton_rafraichissement = str(RefreshToken.for_user(utilisateur_vendeur))

    premiere_reponse = publier_deconnexion(jeton_acces, jeton_rafraichissement)
    seconde_reponse = publier_deconnexion(jeton_acces, jeton_rafraichissement)

    assert premiere_reponse.status_code == 204
    assert seconde_reponse.status_code == 204
    assert (
        JournalSecurite.objects.filter(
            type_evenement=TypeEvenementSecurite.DECONNEXION,
        ).count()
        == 2
    )


@pytest.mark.django_db
def test_deconnexion_refuse_le_jeton_d_un_autre_utilisateur(utilisateur_vendeur):
    autre_utilisateur = UtilisateurFabrique()
    jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))
    jeton_rafraichissement = str(RefreshToken.for_user(autre_utilisateur))

    reponse = publier_deconnexion(jeton_acces, jeton_rafraichissement)

    assert reponse.status_code == 403
    assert reponse.data["code"] == "jeton_non_autorise"
    assert not JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.DECONNEXION,
    ).exists()
    assert jeton_rafraichissement not in str(reponse.data)


@pytest.mark.django_db
def test_jeton_de_rafraichissement_malforme_est_refuse(utilisateur_vendeur):
    jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))

    reponse = publier_deconnexion(jeton_acces, "pas.un.jwt")

    assert reponse.status_code == 400
    assert reponse.data["code"] == "jeton_invalide"
    evenement = JournalSecurite.objects.get(type_evenement=TypeEvenementSecurite.ACCES_REFUSE)
    assert evenement.details == {"raison": "jeton_invalide"}
    assert "pas.un.jwt" not in str(evenement.details)


@pytest.mark.django_db
def test_jeton_access_ne_peut_pas_etre_revoque_comme_un_refresh(utilisateur_vendeur):
    jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))
    jeton_acces_authentification = str(AccessToken.for_user(utilisateur_vendeur))

    reponse = publier_deconnexion(jeton_acces_authentification, jeton_acces)

    assert reponse.status_code == 400
    assert reponse.data["code"] == "jeton_invalide"


@pytest.mark.django_db
def test_jeton_refresh_expire_est_refuse(utilisateur_vendeur):
    with freeze_time("2026-01-01T00:00:00Z"):
        jeton_expirant = str(RefreshToken.for_user(utilisateur_vendeur))

    with freeze_time("2026-01-09T00:00:00Z"):
        jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))
        reponse = publier_deconnexion(jeton_acces, jeton_expirant)

    assert reponse.status_code == 400
    assert reponse.data["code"] == "jeton_invalide"


@pytest.mark.django_db
def test_deconnexion_anonyme_est_refuse(utilisateur_vendeur):
    jeton_rafraichissement = str(RefreshToken.for_user(utilisateur_vendeur))

    reponse = publier_deconnexion(None, jeton_rafraichissement)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "non_authentifie"
    assert reponse["WWW-Authenticate"].startswith("Bearer")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "corps",
    [
        {},
        {"refresh": ""},
        {"refresh": "pas.un.jwt", "role": "admin"},
    ],
)
def test_corps_invalide_est_refuse_sans_reveler_de_jeton(utilisateur_vendeur, corps):
    jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton_acces}")

    reponse = client.post(ROUTE_DECONNEXION, corps, format="json")

    assert reponse.status_code == 400
    assert reponse.data["code"] in {"donnees_invalides", "champs_inconnus"}


@pytest.mark.django_db
def test_limitation_debit_deconnexion_est_appliquee(utilisateur_vendeur):
    jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))
    jeton_rafraichissement = str(RefreshToken.for_user(utilisateur_vendeur))
    limites = {
        **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
        "deconnexion": "0/min",
    }

    with override_settings(
        REST_FRAMEWORK={
            **settings.REST_FRAMEWORK,
            "DEFAULT_THROTTLE_RATES": limites,
        }
    ):
        reponse = publier_deconnexion(jeton_acces, jeton_rafraichissement)

    assert reponse.status_code == 429
    assert reponse.data["code"] == "trop_de_requetes"
    assert "Retry-After" in reponse


@pytest.mark.django_db
def test_get_est_interdit(utilisateur_vendeur):
    jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton_acces}")

    reponse = client.get(ROUTE_DECONNEXION)

    assert reponse.status_code == 405
    assert reponse.data["code"] == "methode_non_autorisee"
