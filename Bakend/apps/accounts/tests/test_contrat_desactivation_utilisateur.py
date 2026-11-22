"""Vérifie les réponses documentées pour la désactivation utilisateur."""

import uuid

import pytest
from django.core.cache import cache
from drf_spectacular.generators import SchemaGenerator
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.exemples_json import EXEMPLES_JSON_DESACTIVATION_UTILISATEUR
from apps.accounts.services import DernierAdministrateurActif
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.tests.test_creation_utilisateur import client_administrateur
from apps.accounts.tests.test_desactivation_utilisateur import ROUTE_DESACTIVATION
from apps.conftest import UtilisateurFabrique

_STATUTS_HTTP = {
    "desactivation_succes": 200,
    "desactivation_corps_interdit": 400,
    "desactivation_non_authentifie": 401,
    "desactivation_jeton_invalide": 401,
    "desactivation_jeton_expire": 401,
    "desactivation_acces_interdit": 403,
    "desactivation_changement_mot_de_passe_requis": 403,
    "desactivation_auto_interdite": 403,
    "desactivation_uuid_invalide": 404,
    "desactivation_utilisateur_introuvable": 404,
    "desactivation_methode_interdite": 405,
    "desactivation_dernier_administrateur": 409,
    "desactivation_deja_inactif": 409,
    "desactivation_limite_atteinte": 429,
    "desactivation_erreur_interne": 500,
}


@pytest.fixture(autouse=True)
def vider_cache_contrat_desactivation():
    cache.clear()


@pytest.mark.django_db
@pytest.mark.parametrize("cas", tuple(_STATUTS_HTTP))
def test_reponse_reelle_correspond_a_l_exemple_catalogue(
    cas,
    utilisateur_vendeur,
    monkeypatch,
):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique(email="cible@exemple.test")
    route = ROUTE_DESACTIVATION.format(uuid=cible.uuid)

    if cas == "desactivation_succes":
        cible.email = "rakoto@exemple.com"
        cible.nom = "Rakoto"
        cible.prenom = "Hery"
        cible.telephone = "+261320000000"
        cible.save(update_fields=["email", "nom", "prenom", "telephone"])
        reponse = client.post(route)
    elif cas == "desactivation_corps_interdit":
        reponse = client.post(route, {"est_actif": True}, format="json")
    elif cas == "desactivation_non_authentifie":
        reponse = APIClient().post(route)
    elif cas in {"desactivation_jeton_invalide", "desactivation_jeton_expire"}:
        if cas == "desactivation_jeton_invalide":
            jeton = str(AccessToken.for_user(utilisateur_vendeur))
            jeton = f"{jeton[:-1]}{'A' if jeton[-1] != 'A' else 'B'}"
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
            reponse = client.post(route)
        else:
            with freeze_time("2026-01-01T00:00:00Z"):
                jeton = str(AccessToken.for_user(utilisateur_vendeur))
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
            with freeze_time("2026-01-01T00:16:00Z"):
                reponse = client.post(route)
    elif cas == "desactivation_acces_interdit":
        vendeur = UtilisateurFabrique()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(vendeur)}",
        )
        reponse = client.post(route)
    elif cas == "desactivation_changement_mot_de_passe_requis":
        utilisateur_vendeur.doit_changer_mot_de_passe = True
        utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
        )
        reponse = client.post(route)
    elif cas == "desactivation_auto_interdite":
        reponse = client.post(
            ROUTE_DESACTIVATION.format(uuid=utilisateur_vendeur.uuid),
        )
    elif cas == "desactivation_uuid_invalide":
        reponse = client.post(
            ROUTE_DESACTIVATION.format(uuid="pas-un-uuid"),
        )
    elif cas == "desactivation_utilisateur_introuvable":
        reponse = client.post(ROUTE_DESACTIVATION.format(uuid=uuid.uuid4()))
    elif cas == "desactivation_methode_interdite":
        reponse = client.get(route)
    elif cas == "desactivation_dernier_administrateur":

        def dernier_admin(*args, **kwargs):
            raise DernierAdministrateurActif()

        monkeypatch.setattr(
            "apps.accounts.views.desactivation.desactiver_utilisateur_par_administrateur",
            dernier_admin,
        )
        reponse = client.post(route)
    elif cas == "desactivation_deja_inactif":
        cible.is_active = False
        cible.save(update_fields=["is_active"])
        reponse = client.post(route)
    elif cas == "desactivation_limite_atteinte":
        monkeypatch.setattr(
            UserRateThrottle,
            "allow_request",
            lambda throttle, requete, vue: False,
        )
        monkeypatch.setattr(UserRateThrottle, "wait", lambda throttle: 60)
        reponse = client.post(route)
    else:

        def provoquer_erreur(*args, **kwargs):
            raise RuntimeError("détail technique non exposable")

        monkeypatch.setattr(
            "apps.accounts.views.desactivation.desactiver_utilisateur_par_administrateur",
            provoquer_erreur,
        )
        reponse = client.post(route)

    assert reponse.status_code == _STATUTS_HTTP[cas]
    verifier_forme_json(reponse, EXEMPLES_JSON_DESACTIVATION_UTILISATEUR[cas])
    if cas == "desactivation_limite_atteinte":
        assert reponse["Retry-After"] == "60"


def test_swagger_documente_tous_les_resultats_de_desactivation():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/users/{uuid}/deactivate/"]["post"]

    assert set(operation["responses"]) == {
        "200",
        "400",
        "401",
        "403",
        "404",
        "405",
        "409",
        "429",
        "500",
    }
    assert operation.get("security")
    assert "requestBody" not in operation
