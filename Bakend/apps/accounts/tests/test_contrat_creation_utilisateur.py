"""Vérifie les réponses réelles contre les exemples OpenAPI de création utilisateur."""

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.exemples_json import EXEMPLES_JSON_CREATION_UTILISATEUR
from apps.accounts.services import ConflitEmail
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.tests.test_creation_utilisateur import (
    MOT_DE_PASSE_INITIAL,
    ROUTE_CREATION_UTILISATEUR,
    client_administrateur,
    payload_utilisateur,
)

_STATUTS_HTTP = {
    "creation_succes": 201,
    "creation_email_invalide": 400,
    "creation_mot_de_passe_faible": 400,
    "creation_role_invalide": 400,
    "creation_champs_inconnus": 400,
    "creation_json_malforme": 400,
    "creation_non_authentifie": 401,
    "creation_jeton_invalide": 401,
    "creation_jeton_expire": 401,
    "creation_acces_interdit": 403,
    "creation_changement_mot_de_passe_requis": 403,
    "creation_methode_interdite": 405,
    "creation_email_deja_utilise": 409,
    "creation_type_contenu": 415,
    "creation_limite_atteinte": 429,
    "creation_erreur_interne": 500,
}


@pytest.fixture(autouse=True)
def vider_cache_creation_utilisateur():
    cache.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("cas", tuple(_STATUTS_HTTP))
def test_reponse_reelle_conforme_a_l_exemple_documente(
    cas,
    utilisateur_vendeur,
    monkeypatch,
):
    client = client_administrateur(utilisateur_vendeur)

    if cas == "creation_succes":
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            {
                "email": "rakoto@exemple.com",
                "nom": "Rakoto",
                "prenom": "Hery",
                "telephone": "+261320000000",
                "role": "vendeur",
                "mot_de_passe_initial": MOT_DE_PASSE_INITIAL,
            },
            format="json",
        )
    elif cas == "creation_email_invalide":
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(email="adresse-invalide"),
            format="json",
        )
    elif cas == "creation_mot_de_passe_faible":
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(mot_de_passe_initial="court"),
            format="json",
        )
    elif cas == "creation_role_invalide":
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(role="superadmin"),
            format="json",
        )
    elif cas == "creation_champs_inconnus":
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(is_superuser=True),
            format="json",
        )
    elif cas == "creation_json_malforme":
        reponse = client.generic(
            "POST",
            ROUTE_CREATION_UTILISATEUR,
            data=b'{"email":',
            content_type="application/json",
        )
    elif cas == "creation_non_authentifie":
        reponse = APIClient().post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(),
            format="json",
        )
    elif cas == "creation_jeton_invalide":
        jeton = str(AccessToken.for_user(utilisateur_vendeur))
        jeton_falsifie = f"{jeton[:-1]}{'A' if jeton[-1] != 'A' else 'B'}"
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton_falsifie}")
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(),
            format="json",
        )
    elif cas == "creation_jeton_expire":
        with freeze_time("2026-01-01T00:00:00Z"):
            jeton = str(AccessToken.for_user(utilisateur_vendeur))
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
        with freeze_time("2026-01-01T00:16:00Z"):
            reponse = client.post(
                ROUTE_CREATION_UTILISATEUR,
                payload_utilisateur(),
                format="json",
            )
    elif cas == "creation_acces_interdit":
        utilisateur_vendeur.role = "vendeur"
        utilisateur_vendeur.save(update_fields=["role"])
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
        )
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(),
            format="json",
        )
    elif cas == "creation_changement_mot_de_passe_requis":
        utilisateur_vendeur.doit_changer_mot_de_passe = True
        utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
        )
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(),
            format="json",
        )
    elif cas == "creation_methode_interdite":
        reponse = client.delete(ROUTE_CREATION_UTILISATEUR)
    elif cas == "creation_email_deja_utilise":

        def simuler_conflit(*args, **kwargs):
            raise ConflitEmail

        monkeypatch.setattr(
            "apps.accounts.views.creation.creer_utilisateur_par_administrateur",
            simuler_conflit,
        )
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(),
            format="json",
        )
    elif cas == "creation_type_contenu":
        reponse = client.generic(
            "POST",
            ROUTE_CREATION_UTILISATEUR,
            data="email=rakoto%40exemple.com",
            content_type="text/plain",
        )
    elif cas == "creation_limite_atteinte":
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
            reponse = client.post(
                ROUTE_CREATION_UTILISATEUR,
                payload_utilisateur(),
                format="json",
            )
    else:

        def provoquer_erreur(*args, **kwargs):
            raise RuntimeError("détail technique non exposable")

        monkeypatch.setattr(
            "apps.accounts.views.creation.creer_utilisateur_par_administrateur",
            provoquer_erreur,
        )
        reponse = client.post(
            ROUTE_CREATION_UTILISATEUR,
            payload_utilisateur(),
            format="json",
        )

    assert reponse.status_code == _STATUTS_HTTP[cas]
    verifier_forme_json(reponse, EXEMPLES_JSON_CREATION_UTILISATEUR[cas])


def test_swagger_documente_tous_les_resultats_de_creation_utilisateur():
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/users/"]["post"]

    assert set(operation["responses"]) == {
        "201",
        "400",
        "401",
        "403",
        "405",
        "409",
        "415",
        "429",
        "500",
    }
    assert operation.get("security")
