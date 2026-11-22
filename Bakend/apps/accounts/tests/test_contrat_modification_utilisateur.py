"""Vérifie les réponses documentées pour la modification utilisateur."""

import uuid

import pytest
from django.core.cache import cache
from drf_spectacular.generators import SchemaGenerator
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.exemples_json import EXEMPLES_JSON_MODIFICATION_UTILISATEUR
from apps.accounts.services import ConflitEmail, DernierAdministrateur
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.tests.test_creation_utilisateur import client_administrateur
from apps.accounts.tests.test_modification_utilisateur import ROUTE_MODIFICATION
from apps.conftest import UtilisateurFabrique

_STATUTS_HTTP = {
    "modification_succes": 200,
    "modification_validation": 400,
    "modification_champs_inconnus": 400,
    "modification_json_malforme": 400,
    "modification_type_contenu": 415,
    "modification_non_authentifie": 401,
    "modification_jeton_invalide": 401,
    "modification_jeton_expire": 401,
    "modification_acces_interdit": 403,
    "modification_changement_mot_de_passe_requis": 403,
    "modification_role_propre_interdit": 403,
    "modification_uuid_invalide": 404,
    "modification_utilisateur_introuvable": 404,
    "modification_methode_interdite": 405,
    "modification_email_conflit": 409,
    "modification_dernier_administrateur": 409,
    "modification_limite_atteinte": 429,
    "modification_erreur_interne": 500,
}


@pytest.fixture(autouse=True)
def vider_cache_contrat_modification():
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
    route = ROUTE_MODIFICATION.format(uuid=cible.uuid)

    if cas == "modification_succes":
        cible.email = "rakoto@exemple.com"
        cible.telephone = "+261320000000"
        cible.save(update_fields=["email", "telephone"])
        reponse = client.patch(route, {"nom": "Rakoto"}, format="json")
    elif cas == "modification_validation":
        reponse = client.patch(route, {"email": "adresse-invalide"}, format="json")
    elif cas == "modification_champs_inconnus":
        reponse = client.patch(route, {"mot_de_passe": "interdit"}, format="json")
    elif cas == "modification_json_malforme":
        reponse = client.generic("PATCH", route, data="{", content_type="application/json")
    elif cas == "modification_type_contenu":
        reponse = client.generic("PATCH", route, data="nom", content_type="text/plain")
    elif cas == "modification_non_authentifie":
        reponse = APIClient().patch(route, {"nom": "Rakoto"}, format="json")
    elif cas in {"modification_jeton_invalide", "modification_jeton_expire"}:
        if cas == "modification_jeton_invalide":
            jeton = str(AccessToken.for_user(utilisateur_vendeur))
            jeton = f"{jeton[:-1]}{'A' if jeton[-1] != 'A' else 'B'}"
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
            reponse = client.patch(route, {"nom": "Rakoto"}, format="json")
        else:
            with freeze_time("2026-01-01T00:00:00Z"):
                jeton = str(AccessToken.for_user(utilisateur_vendeur))
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
            with freeze_time("2026-01-01T00:16:00Z"):
                reponse = client.patch(route, {"nom": "Rakoto"}, format="json")
    elif cas == "modification_acces_interdit":
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(UtilisateurFabrique())}",
        )
        reponse = client.patch(route, {"nom": "Rakoto"}, format="json")
    elif cas == "modification_changement_mot_de_passe_requis":
        utilisateur_vendeur.doit_changer_mot_de_passe = True
        utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
        )
        reponse = client.patch(route, {"nom": "Rakoto"}, format="json")
    elif cas == "modification_role_propre_interdit":
        reponse = client.patch(
            ROUTE_MODIFICATION.format(uuid=utilisateur_vendeur.uuid),
            {"role": "vendeur"},
            format="json",
        )
    elif cas == "modification_uuid_invalide":
        reponse = client.patch(
            ROUTE_MODIFICATION.format(uuid="pas-un-uuid"),
            {"nom": "Rakoto"},
            format="json",
        )
    elif cas == "modification_utilisateur_introuvable":
        reponse = client.patch(
            ROUTE_MODIFICATION.format(uuid=uuid.uuid4()),
            {"nom": "Rakoto"},
            format="json",
        )
    elif cas == "modification_methode_interdite":
        reponse = client.put(route, {"nom": "Rakoto"}, format="json")
    elif cas == "modification_email_conflit":

        def conflit(*args, **kwargs):
            raise ConflitEmail()

        monkeypatch.setattr(
            "apps.accounts.views.detail.modifier_utilisateur_par_administrateur",
            conflit,
        )
        reponse = client.patch(route, {"email": "pris@exemple.test"}, format="json")
    elif cas == "modification_dernier_administrateur":

        def dernier_admin(*args, **kwargs):
            raise DernierAdministrateur()

        monkeypatch.setattr(
            "apps.accounts.views.detail.modifier_utilisateur_par_administrateur",
            dernier_admin,
        )
        reponse = client.patch(route, {"role": "vendeur"}, format="json")
    elif cas == "modification_limite_atteinte":
        monkeypatch.setattr(
            UserRateThrottle,
            "allow_request",
            lambda throttle, requete, vue: False,
        )
        monkeypatch.setattr(UserRateThrottle, "wait", lambda throttle: 60)
        reponse = client.patch(route, {"nom": "Rakoto"}, format="json")
    else:

        def provoquer_erreur(*args, **kwargs):
            raise RuntimeError("détail technique non exposable")

        monkeypatch.setattr(
            "apps.accounts.views.detail.modifier_utilisateur_par_administrateur",
            provoquer_erreur,
        )
        reponse = client.patch(route, {"nom": "Rakoto"}, format="json")

    assert reponse.status_code == _STATUTS_HTTP[cas]
    verifier_forme_json(reponse, EXEMPLES_JSON_MODIFICATION_UTILISATEUR[cas])
    if cas == "modification_limite_atteinte":
        assert reponse["Retry-After"] == "60"


def test_swagger_documente_tous_les_resultats_de_modification():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/users/{uuid}/"]["patch"]

    assert set(operation["responses"]) == {
        "200",
        "400",
        "401",
        "403",
        "404",
        "405",
        "409",
        "415",
        "429",
        "500",
    }
    assert operation.get("security")
    assert operation["requestBody"]["content"]["application/json"]["examples"]
