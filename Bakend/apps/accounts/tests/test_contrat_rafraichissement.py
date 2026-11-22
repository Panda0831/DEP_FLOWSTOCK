"""Vérifie les réponses réelles contre les exemples OpenAPI de renouvellement."""

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.exemples_json import EXEMPLES_JSON_RAFRAICHISSEMENT
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.tests.test_rafraichissement import ROUTE_RAFRAICHISSEMENT

_STATUTS_HTTP = {
    "rafraichissement_succes": 200,
    "rafraichissement_validation": 400,
    "rafraichissement_champs_inconnus": 400,
    "rafraichissement_json_malforme": 400,
    "rafraichissement_jeton_invalide": 401,
    "rafraichissement_jeton_expire": 401,
    "rafraichissement_methode_interdite": 405,
    "rafraichissement_type_contenu": 415,
    "rafraichissement_limite_atteinte": 429,
    "rafraichissement_erreur_interne": 500,
}


@pytest.fixture(autouse=True)
def vider_cache_renouvellement():
    cache.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("cas", tuple(_STATUTS_HTTP))
def test_reponse_reelle_conforme_a_l_exemple_documente(cas, utilisateur_vendeur, monkeypatch):
    client = APIClient()
    jeton = str(RefreshToken.for_user(utilisateur_vendeur))

    if cas == "rafraichissement_succes":
        reponse = client.post(ROUTE_RAFRAICHISSEMENT, {"refresh": jeton}, format="json")
    elif cas == "rafraichissement_validation":
        reponse = client.post(ROUTE_RAFRAICHISSEMENT, {}, format="json")
    elif cas == "rafraichissement_champs_inconnus":
        reponse = client.post(
            ROUTE_RAFRAICHISSEMENT,
            {"refresh": jeton, "role": "admin"},
            format="json",
        )
    elif cas == "rafraichissement_json_malforme":
        reponse = client.generic(
            "POST",
            ROUTE_RAFRAICHISSEMENT,
            data=b'{"refresh":',
            content_type="application/json",
        )
    elif cas == "rafraichissement_jeton_invalide":
        reponse = client.post(ROUTE_RAFRAICHISSEMENT, {"refresh": "pas.un.jwt"}, format="json")
    elif cas == "rafraichissement_jeton_expire":
        with freeze_time("2026-01-01T00:00:00Z"):
            jeton_expirant = str(RefreshToken.for_user(utilisateur_vendeur))
        with freeze_time("2026-01-09T00:00:00Z"):
            reponse = client.post(
                ROUTE_RAFRAICHISSEMENT,
                {"refresh": jeton_expirant},
                format="json",
            )
    elif cas == "rafraichissement_methode_interdite":
        reponse = client.get(ROUTE_RAFRAICHISSEMENT)
    elif cas == "rafraichissement_type_contenu":
        reponse = client.generic(
            "POST",
            ROUTE_RAFRAICHISSEMENT,
            data="refresh=token",
            content_type="text/plain",
        )
    elif cas == "rafraichissement_limite_atteinte":
        limites = {
            **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
            "rafraichissement": "0/min",
        }
        with override_settings(
            REST_FRAMEWORK={
                **settings.REST_FRAMEWORK,
                "DEFAULT_THROTTLE_RATES": limites,
            }
        ):
            reponse = client.post(ROUTE_RAFRAICHISSEMENT, {"refresh": jeton}, format="json")
    else:

        def provoquer_erreur(*args, **kwargs):
            raise RuntimeError("détail technique non exposable")

        monkeypatch.setattr(
            "apps.accounts.views.jetons.rafraichir_jetons",
            provoquer_erreur,
        )
        reponse = client.post(ROUTE_RAFRAICHISSEMENT, {"refresh": jeton}, format="json")

    assert reponse.status_code == _STATUTS_HTTP[cas]
    verifier_forme_json(reponse, EXEMPLES_JSON_RAFRAICHISSEMENT[cas])
