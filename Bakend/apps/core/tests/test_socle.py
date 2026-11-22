"""Vérifie les protections HTTP et les composants transverses du socle."""

import hashlib
import logging
from types import SimpleNamespace

import pytest
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpResponse
from django.test import Client, RequestFactory, override_settings
from rest_framework import exceptions, serializers, status
from rest_framework.request import Request

from apps.accounts.models import RoleUtilisateur
from apps.accounts.permissions import (
    ChangementMotDePasseNonRequis,
    EstAdministrateur,
    EstVendeur,
)
from apps.core.exceptions import gestionnaire_exceptions
from apps.core.middleware import CacheNoStoreMiddleware
from apps.core.mixins import RefusChampsInconnusMixin
from apps.core.pagination import PaginationStandard
from apps.core.reseau import adresse_ip_client
from apps.core.throttling import LimitationParCleStable
from apps.core.validators import LongueurMaximaleMotDePasseValidator


class LimitationTest(LimitationParCleStable):
    """Limitation minimale pour tester le format de périodes étendu."""

    scope = "connexion_par_email"

    def cle_client(self, requete) -> str:
        """Retourne une clé de test fixe."""
        return "cle-test"


class LimitationSansCleTest(LimitationTest):
    """Limitation dont l’identifiant est volontairement absent."""

    def cle_client(self, requete) -> None:
        """Indique qu’aucune clé stable n’est disponible."""
        return None


class LimitationSansImplementation(LimitationParCleStable):
    """Limitation de test qui n’implémente pas sa clé métier."""

    scope = "user"


class LimitationTauxManquant(LimitationParCleStable):
    """Limitation de test sans taux configuré."""

    scope = "taux_absent"


class SerializerTest(RefusChampsInconnusMixin, serializers.Serializer):
    """Serializer minimal pour vérifier le refus des champs inconnus."""

    nom = serializers.CharField()


def test_validateur_refuse_un_mot_de_passe_trop_long():
    validateur = LongueurMaximaleMotDePasseValidator()

    with pytest.raises(ValidationError, match="ne peut pas dépasser"):
        validateur.validate("a" * 129)


def test_validateur_accepte_la_longueur_maximale():
    validateur = LongueurMaximaleMotDePasseValidator()
    validateur.validate("a" * 128)
    assert "128" in validateur.get_help_text()


def test_limitation_interprete_correctement_les_periodes_de_quinze_minutes():
    limitation = LimitationTest()

    assert limitation.rate == "5/15min"
    assert limitation.duration == 900


def test_limitation_accepte_le_taux_absent_et_refuse_un_format_invalide():
    limitation = LimitationTest()

    assert limitation.parse_rate(None) == (None, None)
    with pytest.raises(ImproperlyConfigured, match="Limite de débit invalide"):
        limitation.parse_rate("invalide")
    assert LimitationSansCleTest().get_cache_key(None, None) is None
    empreinte = hashlib.sha256(b"cle-test").hexdigest()
    assert LimitationTest().get_cache_key(None, None) == (
        f"throttle_connexion_par_email_{empreinte}"
    )
    with pytest.raises(NotImplementedError):
        LimitationSansImplementation().get_cache_key(None, None)


def test_limitation_refuse_un_scope_sans_taux_configure():
    with pytest.raises(ImproperlyConfigured, match="Aucun taux de limitation configuré"):
        LimitationTauxManquant()


def test_serializer_refuse_les_champs_inconnus():
    serializer = SerializerTest(data={"nom": "Rakoto", "is_superuser": True})

    assert not serializer.is_valid()
    assert "champs_inconnus" in serializer.errors


def test_serializer_accepte_sa_liste_blanche():
    serializer = SerializerTest(data={"nom": "Rakoto"})

    assert serializer.is_valid()
    assert serializer.validated_data == {"nom": "Rakoto"}


def test_serializer_transmet_les_types_de_corps_non_dictionnaires_a_drf():
    with pytest.raises(serializers.ValidationError):
        SerializerTest().to_internal_value(["Rakoto"])


def test_pagination_applique_une_taille_bornee():
    request = Request(RequestFactory().get("/api/v1/users/?page_size=500"))

    assert PaginationStandard().get_page_size(request) == 100


def test_adresse_ip_ne_fait_pas_confiance_au_transfert_sans_proxy():
    requete = RequestFactory().get(
        "/",
        HTTP_X_FORWARDED_FOR="203.0.113.8",
        REMOTE_ADDR="192.0.2.4",
    )

    with override_settings(REST_FRAMEWORK={"NUM_PROXIES": 0}):
        assert adresse_ip_client(requete) == "192.0.2.4"


def test_adresse_ip_selectionne_le_client_selon_le_nombre_de_proxies():
    requete = RequestFactory().get(
        "/",
        HTTP_X_FORWARDED_FOR="203.0.113.8, 198.51.100.2",
        REMOTE_ADDR="192.0.2.4",
    )

    with override_settings(REST_FRAMEWORK={"NUM_PROXIES": 1}):
        assert adresse_ip_client(requete) == "203.0.113.8"


def test_adresse_ip_ignore_une_chaine_transferee_trop_courte():
    requete = RequestFactory().get(
        "/",
        HTTP_X_FORWARDED_FOR="203.0.113.8",
        REMOTE_ADDR="192.0.2.4",
    )

    with override_settings(REST_FRAMEWORK={"NUM_PROXIES": 1}):
        assert adresse_ip_client(requete) == "192.0.2.4"


def test_adresse_ip_refuse_une_adresse_transferee_invalide():
    requete = RequestFactory().get(
        "/",
        HTTP_X_FORWARDED_FOR="adresse-invalide, 198.51.100.2",
        REMOTE_ADDR="192.0.2.4",
    )

    with override_settings(REST_FRAMEWORK={"NUM_PROXIES": 1}):
        assert adresse_ip_client(requete) is None


def test_adresse_ip_retourne_none_sans_adresse_distante():
    requete = RequestFactory().get("/", REMOTE_ADDR="")

    with override_settings(REST_FRAMEWORK={"NUM_PROXIES": 0}):
        assert adresse_ip_client(requete) is None


def test_middleware_empeche_le_cache_des_routes_sensibles():
    requete = RequestFactory().get("/api/v1/auth/me/")
    middleware = CacheNoStoreMiddleware(lambda requete: HttpResponse("ok"))

    reponse = middleware(requete)

    assert reponse["Cache-Control"] == "no-store"
    assert reponse["Pragma"] == "no-cache"


def test_middleware_ne_modifie_pas_une_route_non_sensible():
    requete = RequestFactory().get("/api/v1/products/")
    reponse = CacheNoStoreMiddleware(lambda requete: HttpResponse("ok"))(requete)

    assert "Cache-Control" not in reponse


def test_documentation_swagger_est_publique_et_schema_valide():
    client = Client()

    reponse_swagger = client.get("/api/v1/docs/")
    reponse_schema = client.get("/api/v1/schema/")

    assert reponse_swagger.status_code == status.HTTP_200_OK
    assert reponse_schema.status_code == status.HTTP_200_OK
    schema = reponse_schema.content.decode()
    assert "openapi: 3.0.3" in schema
    assert "  /api/v1/auth/login/:" in schema


def test_gestionnaire_formate_les_erreurs_validation():
    exception = exceptions.ValidationError({"email": ["Adresse invalide."]})

    reponse = gestionnaire_exceptions(exception, {})

    assert reponse.status_code == status.HTTP_400_BAD_REQUEST
    assert reponse.data == {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"email": ["Adresse invalide."]},
    }


@pytest.mark.parametrize(
    ("exception", "code_http", "code_attendu"),
    [
        (exceptions.NotAuthenticated(), 401, "non_authentifie"),
        (exceptions.PermissionDenied(), 403, "acces_interdit"),
        (exceptions.NotFound(), 404, "introuvable"),
        (exceptions.MethodNotAllowed("GET"), 405, "methode_non_autorisee"),
        (exceptions.Throttled(), 429, "trop_de_requetes"),
    ],
)
def test_gestionnaire_formate_les_erreurs_http_connues(exception, code_http, code_attendu):
    reponse = gestionnaire_exceptions(exception, {})

    assert reponse.status_code == code_http
    assert reponse.data["code"] == code_attendu
    assert isinstance(reponse.data["detail"], str)


def test_gestionnaire_identifie_les_champs_inconnus():
    exception = serializers.ValidationError(
        {"champs_inconnus": ["Champ interdit."]},
        code="champs_inconnus",
    )

    reponse = gestionnaire_exceptions(exception, {})

    assert reponse.data["code"] == "champs_inconnus"


def test_gestionnaire_ne_revele_aucun_detail_de_reponse_500():
    exception = exceptions.APIException("secret technique")
    exception.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    reponse = gestionnaire_exceptions(exception, {})

    assert reponse.data == {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    }


def test_gestionnaire_utilise_un_code_generique_pour_un_statut_inconnu():
    exception = exceptions.APIException("Erreur métier.")
    exception.status_code = status.HTTP_418_IM_A_TEAPOT

    reponse = gestionnaire_exceptions(exception, {})

    assert reponse.status_code == status.HTTP_418_IM_A_TEAPOT
    assert reponse.data["code"] == "erreur"
    assert reponse.data["detail"] == "Erreur métier."


def test_detail_absent_est_remplace_par_un_message_sans_information():
    from apps.core.exceptions import _detail_francais

    assert _detail_francais(exceptions.APIException(), []) == "Une erreur est survenue."


def test_permissions_refusent_et_autorisent_selon_le_role(utilisateur_vendeur):
    fabrique = RequestFactory()
    requete = fabrique.get("/")
    requete.user = utilisateur_vendeur

    assert EstVendeur().has_permission(requete, None)
    assert not EstAdministrateur().has_permission(requete, None)

    utilisateur_vendeur.role = RoleUtilisateur.ADMIN
    assert EstAdministrateur().has_permission(requete, None)
    assert not EstVendeur().has_permission(requete, None)

    requete.user = SimpleNamespace(is_authenticated=False)
    assert not EstAdministrateur().has_permission(requete, None)
    assert not EstVendeur().has_permission(requete, None)


def test_permissions_refusent_un_compte_inactif(utilisateur_vendeur):
    utilisateur_vendeur.is_active = False
    requete = RequestFactory().get("/")
    requete.user = utilisateur_vendeur

    assert not EstAdministrateur().has_permission(requete, None)
    assert not EstVendeur().has_permission(requete, None)


def test_permission_changement_mot_de_passe_limite_les_routes(utilisateur_vendeur):
    permission = ChangementMotDePasseNonRequis()
    vue = SimpleNamespace(autoriser_mot_de_passe_initial=False)

    requete = RequestFactory().get("/api/v1/users/")
    requete.user = utilisateur_vendeur
    assert permission.has_permission(requete, vue)

    utilisateur_vendeur.doit_changer_mot_de_passe = True
    requete = RequestFactory().get("/api/v1/auth/me/")
    requete.user = utilisateur_vendeur
    assert permission.has_permission(requete, vue)

    requete = RequestFactory().patch("/api/v1/auth/me/")
    requete.user = utilisateur_vendeur
    assert not permission.has_permission(requete, vue)

    requete = RequestFactory().post("/api/v1/auth/password/change/")
    requete.user = utilisateur_vendeur
    assert permission.has_permission(requete, vue)

    requete = RequestFactory().post("/api/v1/auth/logout/")
    requete.user = utilisateur_vendeur
    assert permission.has_permission(requete, vue)

    requete = RequestFactory().post("/api/v1/users/")
    requete.user = utilisateur_vendeur
    assert not permission.has_permission(requete, vue)

    requete = RequestFactory().get("/api/v1/users/")
    requete.user = utilisateur_vendeur
    vue.autoriser_mot_de_passe_initial = True
    assert permission.has_permission(requete, vue)

    requete.user = SimpleNamespace(is_authenticated=False)
    assert permission.has_permission(requete, vue)


def test_gestionnaire_ne_revele_pas_les_details_techniques(caplog):
    exception = RuntimeError("secret de test")

    with caplog.at_level(logging.ERROR, logger="stockflow.securite"):
        reponse = gestionnaire_exceptions(exception, {})

    assert reponse.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert reponse.data == {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    }
    assert "secret de test" not in str(reponse.data)
    assert "secret de test" not in caplog.text
