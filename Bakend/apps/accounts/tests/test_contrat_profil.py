"""Vérifie les réponses réelles contre les exemples OpenAPI du profil."""

import pytest
from django.core.cache import cache
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.exemples_json import EXEMPLES_JSON_PROFIL
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.tests.test_profil import ROUTE_PROFIL


@pytest.fixture(autouse=True)
def vider_cache_profil():
    cache.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("cas", tuple(EXEMPLES_JSON_PROFIL))
def test_reponse_reelle_conforme_a_l_exemple_documente(
    cas,
    utilisateur_vendeur,
):
    client = APIClient()

    if cas in {"profil_succes", "profil_sans_connexion"}:
        if cas == "profil_succes":
            utilisateur_vendeur.telephone = "+261320000000"
            utilisateur_vendeur.last_login = timezone.now()
            utilisateur_vendeur.save(update_fields=["telephone", "last_login"])
        jeton = str(AccessToken.for_user(utilisateur_vendeur))
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
        reponse = client.get(ROUTE_PROFIL)
    elif cas == "profil_non_authentifie":
        reponse = client.get(ROUTE_PROFIL)
    elif cas == "profil_jeton_expire":
        with freeze_time("2026-01-01T00:00:00Z"):
            jeton = str(AccessToken.for_user(utilisateur_vendeur))
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
        with freeze_time("2026-01-01T00:16:00Z"):
            reponse = client.get(ROUTE_PROFIL)
    elif cas == "profil_methode_interdite":
        jeton = str(AccessToken.for_user(utilisateur_vendeur))
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
        reponse = client.post(ROUTE_PROFIL, {}, format="json")
    else:
        jeton = str(AccessToken.for_user(utilisateur_vendeur))
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton[:-1]}invalid")
        reponse = client.get(ROUTE_PROFIL)

    attendu = (
        200
        if cas in {"profil_succes", "profil_sans_connexion"}
        else 405
        if cas == "profil_methode_interdite"
        else 401
    )
    assert reponse.status_code == attendu
    verifier_forme_json(reponse, EXEMPLES_JSON_PROFIL[cas])
