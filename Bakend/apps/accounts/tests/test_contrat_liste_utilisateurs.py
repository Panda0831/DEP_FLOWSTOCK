"""Vérifie les réponses réelles contre les exemples OpenAPI de liste utilisateur."""

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.exemples_json import EXEMPLES_JSON_LISTE_UTILISATEURS
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.tests.test_creation_utilisateur import (
    ROUTE_CREATION_UTILISATEUR,
    client_administrateur,
)
from apps.accounts.tests.test_liste_utilisateurs import ROUTE_UTILISATEURS
from apps.conftest import UtilisateurFabrique

_STATUTS_HTTP = {
    "liste_succes": 200,
    "liste_vide": 200,
    "liste_filtre_invalide": 400,
    "liste_tri_invalide": 400,
    "liste_non_authentifie": 401,
    "liste_jeton_invalide": 401,
    "liste_jeton_expire": 401,
    "liste_acces_interdit": 403,
    "liste_changement_mot_de_passe_requis": 403,
    "liste_page_introuvable": 404,
    "liste_methode_interdite": 405,
    "liste_limite_atteinte": 429,
    "liste_erreur_interne": 500,
}


@pytest.fixture(autouse=True)
def vider_cache_liste_utilisateurs():
    cache.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("cas", tuple(_STATUTS_HTTP))
def test_reponse_reelle_conforme_a_l_exemple_documente(
    cas,
    utilisateur_vendeur,
    monkeypatch,
):
    client = client_administrateur(utilisateur_vendeur)

    if cas == "liste_succes":
        UtilisateurFabrique(
            email="rakoto@exemple.com",
            nom="Rakoto",
            prenom="Hery",
            telephone="+261320000000",
        )
        reponse = client.get(ROUTE_UTILISATEURS, {"search": "rakoto@exemple.com"})
    elif cas == "liste_vide":
        reponse = client.get(ROUTE_UTILISATEURS, {"role": "vendeur"})
    elif cas == "liste_filtre_invalide":
        reponse = client.get(ROUTE_UTILISATEURS, {"role": "superadmin"})
    elif cas == "liste_tri_invalide":
        reponse = client.get(ROUTE_UTILISATEURS, {"ordering": "password"})
    elif cas == "liste_non_authentifie":
        reponse = APIClient().get(ROUTE_UTILISATEURS)
    elif cas == "liste_jeton_invalide":
        jeton = str(AccessToken.for_user(utilisateur_vendeur))
        jeton_falsifie = f"{jeton[:-1]}{'A' if jeton[-1] != 'A' else 'B'}"
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton_falsifie}")
        reponse = client.get(ROUTE_UTILISATEURS)
    elif cas == "liste_jeton_expire":
        with freeze_time("2026-01-01T00:00:00Z"):
            jeton = str(AccessToken.for_user(utilisateur_vendeur))
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
        with freeze_time("2026-01-01T00:16:00Z"):
            reponse = client.get(ROUTE_UTILISATEURS)
    elif cas == "liste_acces_interdit":
        utilisateur_vendeur.role = "vendeur"
        utilisateur_vendeur.save(update_fields=["role"])
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
        )
        reponse = client.get(ROUTE_UTILISATEURS)
    elif cas == "liste_changement_mot_de_passe_requis":
        utilisateur_vendeur.doit_changer_mot_de_passe = True
        utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
        )
        reponse = client.get(ROUTE_UTILISATEURS)
    elif cas == "liste_page_introuvable":
        reponse = client.get(ROUTE_UTILISATEURS, {"page": 999})
    elif cas == "liste_methode_interdite":
        reponse = client.delete(ROUTE_CREATION_UTILISATEUR)
    elif cas == "liste_limite_atteinte":
        limites = {
            **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
            "creation_utilisateur": "0/min",
        }
        with override_settings(
            REST_FRAMEWORK={
                **settings.REST_FRAMEWORK,
                "DEFAULT_THROTTLE_RATES": limites,
            }
        ):
            reponse = client.get(ROUTE_UTILISATEURS)
    else:

        def provoquer_erreur(*args, **kwargs):
            raise RuntimeError("détail technique non exposable")

        monkeypatch.setattr(
            "apps.accounts.views.creation.Utilisateur.objects.all",
            provoquer_erreur,
        )
        reponse = client.get(ROUTE_UTILISATEURS)

    assert reponse.status_code == _STATUTS_HTTP[cas]
    verifier_forme_json(reponse, EXEMPLES_JSON_LISTE_UTILISATEURS[cas])


def test_swagger_documente_tous_les_resultats_de_liste_utilisateurs():
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/users/"]["get"]

    assert set(operation["responses"]) == {
        "200",
        "400",
        "401",
        "403",
        "404",
        "405",
        "429",
        "500",
    }
    assert operation.get("security")
    assert {parametre["name"] for parametre in operation["parameters"]} >= {
        "page",
        "page_size",
        "search",
        "role",
        "active",
        "ordering",
    }
