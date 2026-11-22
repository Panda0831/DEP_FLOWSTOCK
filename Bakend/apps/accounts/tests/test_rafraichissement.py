"""Vérifie le renouvellement et la rotation des jetons JWT."""

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models import JournalSecurite, TypeEvenementSecurite

ROUTE_RAFRAICHISSEMENT = "/api/v1/auth/token/refresh/"


@pytest.fixture(autouse=True)
def vider_cache_rafraichissement():
    cache.clear()


def publier_rafraichissement(jeton: str, adresse_ip: str = "192.0.2.40"):
    return APIClient().post(
        ROUTE_RAFRAICHISSEMENT,
        {"refresh": jeton},
        format="json",
        REMOTE_ADDR=adresse_ip,
    )


@pytest.mark.django_db
def test_rafraichissement_reussit_et_met_l_ancien_jeton_sur_liste_noire(
    utilisateur_vendeur,
):
    jeton_initial = str(RefreshToken.for_user(utilisateur_vendeur))

    reponse = publier_rafraichissement(jeton_initial)

    assert reponse.status_code == 200
    assert set(reponse.data) == {"access", "refresh"}
    assert reponse.data["refresh"] != jeton_initial
    assert AccessToken(reponse.data["access"])["utilisateur_uuid"] == str(utilisateur_vendeur.uuid)
    with pytest.raises(TokenError):
        RefreshToken(jeton_initial)
    assert not JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.JETON_REJETE,
    ).exists()
    assert reponse["Cache-Control"] == "no-store"
    assert reponse["Pragma"] == "no-cache"


@pytest.mark.django_db
def test_ancien_jeton_deja_utilise_est_refuse_et_journalise(utilisateur_vendeur):
    jeton_initial = str(RefreshToken.for_user(utilisateur_vendeur))
    assert publier_rafraichissement(jeton_initial).status_code == 200

    reponse = publier_rafraichissement(jeton_initial)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "jeton_invalide"
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.JETON_REJETE,
        succes=False,
    ).exists()


@pytest.mark.django_db
def test_jeton_revoque_est_refuse(utilisateur_vendeur):
    jeton = RefreshToken.for_user(utilisateur_vendeur)
    jeton.blacklist()

    reponse = publier_rafraichissement(str(jeton))

    assert reponse.status_code == 401
    assert reponse.data["code"] == "jeton_invalide"


@pytest.mark.django_db
def test_rafraichissement_refuse_un_compte_desactive(utilisateur_vendeur):
    jeton = str(RefreshToken.for_user(utilisateur_vendeur))
    utilisateur_vendeur.is_active = False
    utilisateur_vendeur.save(update_fields=["is_active"])

    reponse = publier_rafraichissement(jeton)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "jeton_invalide"
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.JETON_REJETE,
        details__raison="compte_inactif",
    ).exists()


@pytest.mark.django_db
def test_jeton_d_acces_n_est_pas_accepte_comme_jeton_de_rafraichissement(
    utilisateur_vendeur,
):
    jeton = str(AccessToken.for_user(utilisateur_vendeur))

    reponse = publier_rafraichissement(jeton)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "jeton_invalide"


@pytest.mark.django_db
def test_jeton_falsifie_est_refuse_sans_reveler_le_jeton(utilisateur_vendeur):
    jeton = str(RefreshToken.for_user(utilisateur_vendeur))
    dernier_caractere = "A" if jeton[-1] != "A" else "B"
    jeton_falsifie = jeton[:-1] + dernier_caractere

    reponse = publier_rafraichissement(jeton_falsifie)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "jeton_invalide"
    assert reponse["WWW-Authenticate"].startswith("Bearer")
    assert reponse["Cache-Control"] == "no-store"
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.JETON_REJETE,
    )
    assert jeton_falsifie not in str(evenement.details)
    assert jeton_falsifie not in reponse.content.decode()
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.JETON_REJETE,
    ).exists()


@pytest.mark.django_db
def test_jeton_expire_retourne_le_code_documente(utilisateur_vendeur):
    with freeze_time("2026-01-01T00:00:00Z"):
        jeton = str(RefreshToken.for_user(utilisateur_vendeur))

    with freeze_time("2026-01-09T00:00:00Z"):
        reponse = publier_rafraichissement(jeton)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "jeton_expire"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "corps",
    [
        {},
        {"refresh": ""},
        {"refresh": 123},
        {"refresh": "x" * 8193},
        {"refresh": "pas.un.jwt", "role": "admin"},
    ],
)
def test_entrees_invalides_sont_refusees_sans_journaliser_le_jeton(corps):
    reponse = APIClient().post(ROUTE_RAFRAICHISSEMENT, corps, format="json")

    assert reponse.status_code == 400
    assert reponse.data["code"] in {"donnees_invalides", "champs_inconnus"}
    evenement = JournalSecurite.objects.get(type_evenement=TypeEvenementSecurite.JETON_REJETE)
    assert "refresh" not in str(evenement.details)
    assert "pas.un.jwt" not in str(evenement.details)


@pytest.mark.django_db
def test_json_malforme_est_journalise_comme_jeton_rejete():
    reponse = APIClient().generic(
        "POST",
        ROUTE_RAFRAICHISSEMENT,
        data=b'{"refresh":',
        content_type="application/json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.JETON_REJETE,
    ).exists()


@pytest.mark.django_db
def test_get_est_interdit():
    reponse = APIClient().get(ROUTE_RAFRAICHISSEMENT)

    assert reponse.status_code == 405
    assert reponse.data["code"] == "methode_non_autorisee"


@pytest.mark.django_db
def test_limitation_de_debit_rafraichissement_est_appliquee(utilisateur_vendeur):
    jeton = str(RefreshToken.for_user(utilisateur_vendeur))
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
        reponse = publier_rafraichissement(jeton)

    assert reponse.status_code == 429
    assert reponse.data["code"] == "trop_de_requetes"
    assert "Retry-After" in reponse


def test_swagger_documente_tous_les_resultats_du_renouvellement():
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/auth/token/refresh/"]["post"]

    assert set(operation["responses"]) == {"200", "400", "401", "405", "415", "429", "500"}
    assert operation.get("security", []) == []
