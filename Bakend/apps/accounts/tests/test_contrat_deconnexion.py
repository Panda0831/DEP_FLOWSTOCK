"""Vérifie les réponses réelles contre les exemples OpenAPI de déconnexion."""

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.exemples_json import EXEMPLES_JSON_DECONNEXION
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.tests.test_deconnexion import ROUTE_DECONNEXION
from apps.conftest import UtilisateurFabrique

_STATUTS_HTTP = {
    "deconnexion_succes": 204,
    "deconnexion_validation": 400,
    "deconnexion_champs_inconnus": 400,
    "deconnexion_json_malforme": 400,
    "deconnexion_jeton_invalide": 400,
    "deconnexion_non_authentifie": 401,
    "deconnexion_acces_invalide": 401,
    "deconnexion_acces_expire": 401,
    "deconnexion_jeton_non_autorise": 403,
    "deconnexion_methode_interdite": 405,
    "deconnexion_type_contenu": 415,
    "deconnexion_limite_atteinte": 429,
    "deconnexion_erreur_interne": 500,
}


@pytest.fixture(autouse=True)
def vider_cache_deconnexion():
    cache.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("cas", tuple(_STATUTS_HTTP))
def test_reponse_reelle_conforme_a_l_exemple_documente(
    cas,
    utilisateur_vendeur,
    monkeypatch,
):
    client = APIClient()
    jeton_acces = str(AccessToken.for_user(utilisateur_vendeur))
    jeton_rafraichissement = str(RefreshToken.for_user(utilisateur_vendeur))
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton_acces}")

    if cas == "deconnexion_succes":
        reponse = client.post(
            ROUTE_DECONNEXION,
            {"refresh": jeton_rafraichissement},
            format="json",
        )
    elif cas == "deconnexion_validation":
        reponse = client.post(ROUTE_DECONNEXION, {}, format="json")
    elif cas == "deconnexion_champs_inconnus":
        reponse = client.post(
            ROUTE_DECONNEXION,
            {"refresh": jeton_rafraichissement, "role": "admin"},
            format="json",
        )
    elif cas == "deconnexion_json_malforme":
        reponse = client.generic(
            "POST",
            ROUTE_DECONNEXION,
            data=b'{"refresh":',
            content_type="application/json",
        )
    elif cas == "deconnexion_jeton_invalide":
        reponse = client.post(ROUTE_DECONNEXION, {"refresh": "pas.un.jwt"}, format="json")
    elif cas == "deconnexion_non_authentifie":
        reponse = APIClient().post(
            ROUTE_DECONNEXION,
            {"refresh": jeton_rafraichissement},
            format="json",
        )
    elif cas == "deconnexion_acces_invalide":
        jeton_falsifie = f"{jeton_acces[:-1]}{'A' if jeton_acces[-1] != 'A' else 'B'}"
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton_falsifie}")
        reponse = client.post(
            ROUTE_DECONNEXION,
            {"refresh": jeton_rafraichissement},
            format="json",
        )
    elif cas == "deconnexion_acces_expire":
        with freeze_time("2026-01-01T00:00:00Z"):
            jeton_expirant = str(AccessToken.for_user(utilisateur_vendeur))
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton_expirant}")
        with freeze_time("2026-01-01T00:16:00Z"):
            reponse = client.post(
                ROUTE_DECONNEXION,
                {"refresh": jeton_rafraichissement},
                format="json",
            )
    elif cas == "deconnexion_jeton_non_autorise":
        autre_utilisateur = UtilisateurFabrique()
        jeton_autre = str(RefreshToken.for_user(autre_utilisateur))
        reponse = client.post(ROUTE_DECONNEXION, {"refresh": jeton_autre}, format="json")
    elif cas == "deconnexion_methode_interdite":
        reponse = client.get(ROUTE_DECONNEXION)
    elif cas == "deconnexion_type_contenu":
        reponse = client.generic(
            "POST",
            ROUTE_DECONNEXION,
            data="refresh=token",
            content_type="text/plain",
        )
    elif cas == "deconnexion_limite_atteinte":
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
            reponse = client.post(
                ROUTE_DECONNEXION,
                {"refresh": jeton_rafraichissement},
                format="json",
            )
    else:

        def provoquer_erreur(*args, **kwargs):
            raise RuntimeError("détail technique non exposable")

        monkeypatch.setattr(
            "apps.accounts.views.deconnexion.deconnecter_utilisateur",
            provoquer_erreur,
        )
        reponse = client.post(
            ROUTE_DECONNEXION,
            {"refresh": jeton_rafraichissement},
            format="json",
        )

    assert reponse.status_code == _STATUTS_HTTP[cas]
    if cas == "deconnexion_succes":
        assert reponse.content == b""
        assert reponse.data is None
    else:
        verifier_forme_json(reponse, EXEMPLES_JSON_DECONNEXION[cas])


def test_swagger_documente_tous_les_resultats_de_deconnexion():
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/auth/logout/"]["post"]

    assert set(operation["responses"]) == {
        "204",
        "400",
        "401",
        "403",
        "405",
        "415",
        "429",
        "500",
    }
    assert operation.get("security")
    assert "content" not in operation["responses"]["204"]
