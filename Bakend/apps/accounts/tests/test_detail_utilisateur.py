"""Vérifie la consultation d’un utilisateur par UUID."""

import uuid

import pytest
from django.core.cache import cache
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.exemples_json import EXEMPLES_JSON_DETAIL_UTILISATEUR
from apps.accounts.models import JournalSecurite, TypeEvenementSecurite
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.tests.test_creation_utilisateur import (
    CHAMPS_UTILISATEUR_ADMIN,
    client_administrateur,
)
from apps.conftest import UtilisateurFabrique

ROUTE_UTILISATEUR = "/api/v1/users/{uuid}/"


@pytest.fixture(autouse=True)
def vider_cache_detail_utilisateur():
    cache.clear()


@pytest.mark.django_db
def test_admin_consulte_un_utilisateur_sans_exposer_de_champs_sensibles(
    utilisateur_vendeur,
):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique(
        email="cible@exemple.test",
        nom="Cible",
        prenom="Test",
        telephone="+261320000000",
    )

    reponse = client.get(ROUTE_UTILISATEUR.format(uuid=cible.uuid))

    assert reponse.status_code == 200
    assert set(reponse.data) == CHAMPS_UTILISATEUR_ADMIN
    assert reponse.data == {
        "uuid": str(cible.uuid),
        "email": cible.email,
        "nom": cible.nom,
        "prenom": cible.prenom,
        "telephone": cible.telephone,
        "role": cible.role,
        "est_actif": True,
        "doit_changer_mot_de_passe": False,
        "date_creation": reponse.data["date_creation"],
        "derniere_connexion": None,
        "date_dernier_changement_mot_de_passe": None,
        "date_modification": reponse.data["date_modification"],
    }
    assert not {"id", "password", "is_superuser", "mot_de_passe"} & set(reponse.data)
    assert reponse["Cache-Control"] == "no-store"
    assert reponse["Pragma"] == "no-cache"
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.UTILISATEUR_CONSULTE,
    )
    assert evenement.acteur == utilisateur_vendeur
    assert evenement.utilisateur_cible == cible
    assert evenement.succes is True
    assert evenement.details == {}


@pytest.mark.django_db
def test_admin_peut_consulter_son_propre_compte(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.get(ROUTE_UTILISATEUR.format(uuid=utilisateur_vendeur.uuid))

    assert reponse.status_code == 200
    assert reponse.data["uuid"] == str(utilisateur_vendeur.uuid)
    assert reponse.data["role"] == "admin"


@pytest.mark.django_db
def test_vendeur_ne_peut_pas_consulter_meme_son_propre_compte(utilisateur_vendeur):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}")

    reponse = client.get(ROUTE_UTILISATEUR.format(uuid=utilisateur_vendeur.uuid))

    assert reponse.status_code == 403
    assert reponse.data["code"] == "acces_interdit"
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.ACCES_REFUSE,
    )
    assert evenement.details == {"raison": "acces_interdit"}
    assert evenement.succes is False


@pytest.mark.django_db
def test_anonyme_ne_peut_pas_consulter_un_utilisateur(utilisateur_vendeur):
    reponse = APIClient().get(ROUTE_UTILISATEUR.format(uuid=utilisateur_vendeur.uuid))

    assert reponse.status_code == 401
    assert reponse.data["code"] == "non_authentifie"
    assert reponse["WWW-Authenticate"].startswith("Bearer")


@pytest.mark.django_db
def test_uuid_inconnu_retourne_404_sans_distinguer_autres_comptes(
    utilisateur_vendeur,
):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.get(ROUTE_UTILISATEUR.format(uuid=uuid.uuid4()))

    assert reponse.status_code == 404
    assert reponse.data["code"] == "introuvable"
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.ACCES_REFUSE,
    )
    assert evenement.details == {"raison": "introuvable"}
    assert str(reponse.data).find(str(utilisateur_vendeur.uuid)) == -1


@pytest.mark.django_db
def test_uuid_malforme_retourne_404(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.get(ROUTE_UTILISATEUR.format(uuid="pas-un-uuid"))

    assert reponse.status_code == 404
    assert reponse.data["code"] == "introuvable"
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.ACCES_REFUSE,
    )
    assert evenement.details == {"raison": "introuvable"}


@pytest.mark.django_db
def test_administrateur_oblige_de_changer_son_mot_de_passe_est_bloque(
    utilisateur_vendeur,
):
    client = client_administrateur(utilisateur_vendeur)
    utilisateur_vendeur.doit_changer_mot_de_passe = True
    utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}")

    reponse = client.get(ROUTE_UTILISATEUR.format(uuid=utilisateur_vendeur.uuid))

    assert reponse.status_code == 403
    assert reponse.data["code"] == "changement_mot_de_passe_requis"


def test_swagger_documente_tous_les_resultats_du_detail_utilisateur():
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/users/{uuid}/"]["get"]

    assert set(operation["responses"]) == {"200", "401", "403", "404", "405", "429", "500"}
    assert operation.get("security")
    assert {parametre["name"] for parametre in operation["parameters"]} >= {"uuid"}


_STATUTS_HTTP_DETAIL = {
    "detail_succes": 200,
    "detail_non_authentifie": 401,
    "detail_jeton_invalide": 401,
    "detail_jeton_expire": 401,
    "detail_acces_interdit": 403,
    "detail_changement_mot_de_passe_requis": 403,
    "detail_uuid_invalide": 404,
    "detail_utilisateur_introuvable": 404,
    "detail_methode_interdite": 405,
    "detail_limite_atteinte": 429,
    "detail_erreur_interne": 500,
}


@pytest.mark.django_db
@pytest.mark.parametrize("cas", tuple(_STATUTS_HTTP_DETAIL))
def test_reponse_reelle_conforme_a_l_exemple_documente(
    cas,
    utilisateur_vendeur,
    monkeypatch,
):
    client = client_administrateur(utilisateur_vendeur)
    cible = None
    uuid_cible = utilisateur_vendeur.uuid

    if cas == "detail_succes":
        cible = UtilisateurFabrique(
            email="rakoto@exemple.com",
            nom="Rakoto",
            prenom="Hery",
            telephone="+261320000000",
        )
        uuid_cible = cible.uuid
        reponse = client.get(ROUTE_UTILISATEUR.format(uuid=uuid_cible))
    elif cas == "detail_non_authentifie":
        reponse = APIClient().get(ROUTE_UTILISATEUR.format(uuid=uuid_cible))
    elif cas in {"detail_jeton_invalide", "detail_jeton_expire"}:
        jeton = str(AccessToken.for_user(utilisateur_vendeur))
        if cas == "detail_jeton_invalide":
            jeton = f"{jeton[:-1]}{'A' if jeton[-1] != 'A' else 'B'}"
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
            reponse = client.get(ROUTE_UTILISATEUR.format(uuid=uuid_cible))
        else:
            with freeze_time("2026-01-01T00:00:00Z"):
                jeton = str(AccessToken.for_user(utilisateur_vendeur))
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
            with freeze_time("2026-01-01T00:16:00Z"):
                reponse = client.get(ROUTE_UTILISATEUR.format(uuid=uuid_cible))
    elif cas == "detail_acces_interdit":
        utilisateur_vendeur.role = "vendeur"
        utilisateur_vendeur.save(update_fields=["role"])
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
        )
        reponse = client.get(ROUTE_UTILISATEUR.format(uuid=uuid_cible))
    elif cas == "detail_changement_mot_de_passe_requis":
        utilisateur_vendeur.doit_changer_mot_de_passe = True
        utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
        )
        reponse = client.get(ROUTE_UTILISATEUR.format(uuid=uuid_cible))
    elif cas == "detail_uuid_invalide":
        reponse = client.get(ROUTE_UTILISATEUR.format(uuid="pas-un-uuid"))
    elif cas == "detail_utilisateur_introuvable":
        reponse = client.get(ROUTE_UTILISATEUR.format(uuid=uuid.uuid4()))
    elif cas == "detail_methode_interdite":
        reponse = client.delete(ROUTE_UTILISATEUR.format(uuid=uuid_cible))
    elif cas == "detail_limite_atteinte":
        monkeypatch.setattr(
            UserRateThrottle,
            "allow_request",
            lambda throttle, requete, vue: False,
        )
        monkeypatch.setattr(UserRateThrottle, "wait", lambda throttle: 60)
        reponse = client.get(ROUTE_UTILISATEUR.format(uuid=uuid_cible))
    else:
        client.force_authenticate(user=utilisateur_vendeur)

        def provoquer_erreur(*args, **kwargs):
            raise RuntimeError("détail technique non exposable")

        monkeypatch.setattr(
            "apps.accounts.views.detail.Utilisateur.objects.get",
            provoquer_erreur,
        )
        reponse = client.get(ROUTE_UTILISATEUR.format(uuid=uuid_cible))

    assert reponse.status_code == _STATUTS_HTTP_DETAIL[cas]
    verifier_forme_json(reponse, EXEMPLES_JSON_DETAIL_UTILISATEUR[cas])
    if cas == "detail_limite_atteinte":
        assert reponse["Retry-After"] == "60"
