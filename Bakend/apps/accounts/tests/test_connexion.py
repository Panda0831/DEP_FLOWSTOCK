"""Vérifie le contrat et les protections du point de connexion JWT."""

import logging

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import JournalSecurite, TypeEvenementSecurite

ROUTE_CONNEXION = "/api/v1/auth/login/"
MOT_DE_PASSE_VALIDE = "Fleur!Miroir8472"


def publier_connexion(
    client: APIClient,
    email: str,
    mot_de_passe: str,
    adresse_ip: str = "192.0.2.10",
):
    """Envoie une requête JSON de connexion depuis une adresse IP déterministe."""
    return client.post(
        ROUTE_CONNEXION,
        {"email": email, "mot_de_passe": mot_de_passe},
        format="json",
        REMOTE_ADDR=adresse_ip,
    )


@pytest.fixture(autouse=True)
def vider_cache_connexion():
    cache.clear()


@pytest.mark.django_db
def test_connexion_reussie_retourne_les_jetons_et_le_resume(utilisateur_vendeur):
    reponse = publier_connexion(
        APIClient(),
        utilisateur_vendeur.email,
        MOT_DE_PASSE_VALIDE,
    )

    assert reponse.status_code == 200
    assert set(reponse.data) == {"access", "refresh", "utilisateur"}
    assert reponse.data["utilisateur"] == {
        "uuid": str(utilisateur_vendeur.uuid),
        "email": utilisateur_vendeur.email,
        "nom": utilisateur_vendeur.nom,
        "prenom": utilisateur_vendeur.prenom,
        "role": "vendeur",
        "doit_changer_mot_de_passe": False,
    }

    jeton_acces = AccessToken(reponse.data["access"])
    assert jeton_acces["utilisateur_uuid"] == str(utilisateur_vendeur.uuid)
    assert "email" not in jeton_acces
    assert "role" not in jeton_acces
    assert utilisateur_vendeur.__class__.objects.get(pk=utilisateur_vendeur.pk).last_login
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.CONNEXION_REUSSIE,
        acteur=utilisateur_vendeur,
        succes=True,
    ).exists()
    assert reponse["Cache-Control"] == "no-store"
    assert reponse["Pragma"] == "no-cache"


@pytest.mark.django_db
def test_connexion_accepte_une_adresse_email_avec_une_autre_casse(utilisateur_vendeur):
    reponse = publier_connexion(
        APIClient(),
        utilisateur_vendeur.email.upper(),
        MOT_DE_PASSE_VALIDE,
    )

    assert reponse.status_code == 200


@pytest.mark.django_db
def test_connexion_ne_supprime_pas_les_espaces_du_mot_de_passe(utilisateur_vendeur):
    mot_de_passe_avec_espaces = f" {MOT_DE_PASSE_VALIDE} "
    utilisateur_vendeur.set_password(mot_de_passe_avec_espaces)
    utilisateur_vendeur.save(update_fields=["password"])

    reponse = publier_connexion(
        APIClient(),
        utilisateur_vendeur.email,
        mot_de_passe_avec_espaces,
    )

    assert reponse.status_code == 200


@pytest.mark.django_db
def test_connexion_exige_un_changement_de_mot_de_passe_indique_le_drapeau(
    utilisateur_vendeur,
):
    utilisateur_vendeur.doit_changer_mot_de_passe = True
    utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])

    reponse = publier_connexion(
        APIClient(),
        utilisateur_vendeur.email,
        MOT_DE_PASSE_VALIDE,
    )

    assert reponse.status_code == 200
    assert reponse.data["utilisateur"]["doit_changer_mot_de_passe"] is True


@pytest.mark.django_db
def test_echecs_inconnu_mot_de_passe_et_compte_inactif_sont_identiques(
    utilisateur_vendeur,
):
    from apps.accounts.models import Utilisateur

    compte_inactif = Utilisateur.objects.creer_utilisateur(
        email="inactif@exemple.test",
        mot_de_passe=MOT_DE_PASSE_VALIDE,
        nom="Rakoto",
        prenom="Hery",
        is_active=False,
    )
    client = APIClient()

    reponse_mot_de_passe = publier_connexion(
        client,
        utilisateur_vendeur.email,
        "MotDePasse!Incorrect934",
        "192.0.2.11",
    )
    reponse_email_inconnu = publier_connexion(
        client,
        "inconnu@exemple.test",
        MOT_DE_PASSE_VALIDE,
        "192.0.2.12",
    )
    reponse_compte_inactif = publier_connexion(
        client,
        compte_inactif.email,
        MOT_DE_PASSE_VALIDE,
        "192.0.2.13",
    )

    assert reponse_mot_de_passe.status_code == 401
    assert reponse_mot_de_passe.data == {
        "detail": "E-mail ou mot de passe incorrect.",
        "code": "identifiants_invalides",
    }
    assert reponse_email_inconnu.data == reponse_mot_de_passe.data
    assert reponse_compte_inactif.data == reponse_mot_de_passe.data
    assert reponse_email_inconnu.status_code == reponse_mot_de_passe.status_code
    assert reponse_compte_inactif.status_code == reponse_mot_de_passe.status_code
    assert reponse_mot_de_passe["WWW-Authenticate"].startswith("Bearer")

    motifs = set(
        JournalSecurite.objects.filter(
            type_evenement=TypeEvenementSecurite.CONNEXION_ECHOUEE,
        ).values_list("details__raison", flat=True)
    )
    assert motifs == {"mot_de_passe_incorrect", "email_inconnu", "compte_inactif"}


@pytest.mark.django_db
def test_email_inconnu_declenche_une_verification_de_hash_factice(monkeypatch):
    from apps.accounts import services

    appels = []
    verifier_originale = services.check_password

    def verifier_espion(mot_de_passe, empreinte):
        appels.append(empreinte)
        return verifier_originale(mot_de_passe, empreinte)

    monkeypatch.setattr(services, "check_password", verifier_espion)
    reponse = publier_connexion(
        APIClient(),
        "absent@exemple.test",
        MOT_DE_PASSE_VALIDE,
    )

    assert reponse.status_code == 401
    assert appels == [services._HASH_MOT_DE_PASSE_FICTIF]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("corps", "code_attendu"),
    [
        ({"email": "pas-une-adresse", "mot_de_passe": MOT_DE_PASSE_VALIDE}, "donnees_invalides"),
        ({"email": "valide@exemple.test", "mot_de_passe": ""}, "donnees_invalides"),
        (
            {"email": "valide@exemple.test", "mot_de_passe": "A" * 129},
            "donnees_invalides",
        ),
        (
            {
                "email": "valide@exemple.test",
                "mot_de_passe": MOT_DE_PASSE_VALIDE,
                "role": "admin",
            },
            "champs_inconnus",
        ),
        ({"email": 12, "mot_de_passe": MOT_DE_PASSE_VALIDE}, "donnees_invalides"),
    ],
)
def test_corps_de_connexion_invalides_sont_journalises_sans_secret(
    corps,
    code_attendu,
):
    reponse = APIClient().post(ROUTE_CONNEXION, corps, format="json")

    assert reponse.status_code == 400
    assert reponse.data["code"] == code_attendu
    assert reponse["Cache-Control"] == "no-store"
    evenement = JournalSecurite.objects.get(type_evenement=TypeEvenementSecurite.CONNEXION_ECHOUEE)
    assert "mot_de_passe" not in str(evenement.details)


@pytest.mark.django_db
def test_json_malforme_est_refuse_avec_une_erreur_uniforme():
    reponse = APIClient().generic(
        "POST",
        ROUTE_CONNEXION,
        data=b'{"email":',
        content_type="application/json",
    )

    assert reponse.status_code == 400
    assert reponse.data == {
        "detail": "Le corps JSON est invalide.",
        "code": "donnees_invalides",
        "erreurs": {},
    }
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.CONNEXION_ECHOUEE
    ).exists()


@pytest.mark.django_db
def test_json_non_objet_est_refuse_sans_cle_de_limitation_email():
    reponse = APIClient().generic(
        "POST",
        ROUTE_CONNEXION,
        data=b"[]",
        content_type="application/json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.CONNEXION_ECHOUEE
    ).exists()


@pytest.mark.django_db
def test_type_de_contenu_non_json_est_documente_et_journalise():
    reponse = APIClient().generic(
        "POST",
        ROUTE_CONNEXION,
        data="email=rakoto%40exemple.test",
        content_type="text/plain",
    )

    assert reponse.status_code == 415
    assert reponse.data["code"] == "donnees_invalides"
    assert "erreurs" in reponse.data
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.CONNEXION_ECHOUEE
    ).exists()


@pytest.mark.django_db
def test_get_sur_connexion_retourne_405_et_cache_no_store():
    reponse = APIClient().get(ROUTE_CONNEXION)

    assert reponse.status_code == 405
    assert reponse.data["code"] == "methode_non_autorisee"
    assert reponse["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_connexion_ne_journalise_ni_ne_renvoie_le_mot_de_passe(
    utilisateur_vendeur,
    caplog,
):
    mot_de_passe_secret = "Confidentiel!778899"
    utilisateur_vendeur.set_password(mot_de_passe_secret)
    utilisateur_vendeur.save(update_fields=["password"])

    with caplog.at_level(logging.INFO, logger="stockflow.securite"):
        reponse = publier_connexion(
            APIClient(),
            utilisateur_vendeur.email,
            mot_de_passe_secret,
        )

    assert reponse.status_code == 200
    assert mot_de_passe_secret not in reponse.content.decode()
    assert mot_de_passe_secret not in caplog.text
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.CONNEXION_REUSSIE,
        acteur=utilisateur_vendeur,
    )
    assert mot_de_passe_secret not in str(evenement.details)
    assert mot_de_passe_secret not in evenement.email_saisi


@pytest.mark.django_db
def test_erreur_interne_de_connexion_ne_revele_aucun_detail(
    utilisateur_vendeur,
    monkeypatch,
):
    def provoquer_erreur(*args, **kwargs):
        raise RuntimeError("secret technique")

    monkeypatch.setattr(
        "apps.accounts.services.creer_jetons_connexion",
        provoquer_erreur,
    )

    reponse = publier_connexion(
        APIClient(),
        utilisateur_vendeur.email,
        MOT_DE_PASSE_VALIDE,
    )

    assert reponse.status_code == 500
    assert reponse.data == {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    }
    assert "secret technique" not in reponse.content.decode()
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.CONNEXION_ECHOUEE,
        details__raison="erreur_interne",
    ).exists()


@pytest.mark.django_db
def test_limitation_par_email_s_applique_aussi_aux_comptes_inconnus():
    cache.clear()
    limites = {
        **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
        "anon": "100/min",
        "connexion": "10/min",
        "connexion_par_email": "2/15min",
    }
    with override_settings(
        REST_FRAMEWORK={
            **settings.REST_FRAMEWORK,
            "DEFAULT_THROTTLE_RATES": limites,
        }
    ):
        client = APIClient()
        premieres_reponses = [
            publier_connexion(
                client,
                "absent@exemple.test",
                MOT_DE_PASSE_VALIDE,
                adresse_ip=f"192.0.2.{numero}",
            )
            for numero in (21, 22)
        ]
        reponse_limitee = publier_connexion(
            client,
            "absent@exemple.test",
            MOT_DE_PASSE_VALIDE,
            adresse_ip="192.0.2.23",
        )

    assert [reponse.status_code for reponse in premieres_reponses] == [401, 401]
    assert reponse_limitee.status_code == 429
    assert reponse_limitee.data["code"] == "trop_de_requetes"
    assert "Retry-After" in reponse_limitee


@pytest.mark.django_db
def test_limitation_par_adresse_ip_s_applique_aux_emails_differents():
    cache.clear()
    limites = {
        **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
        "anon": "100/min",
        "connexion": "2/min",
        "connexion_par_email": "100/15min",
    }
    with override_settings(
        REST_FRAMEWORK={
            **settings.REST_FRAMEWORK,
            "DEFAULT_THROTTLE_RATES": limites,
        }
    ):
        client = APIClient()
        for numero in (31, 32):
            publier_connexion(
                client,
                f"absent-{numero}@exemple.test",
                MOT_DE_PASSE_VALIDE,
                adresse_ip="198.51.100.10",
            )
        reponse_limitee = publier_connexion(
            client,
            "absent-33@exemple.test",
            MOT_DE_PASSE_VALIDE,
            adresse_ip="198.51.100.10",
        )

    assert reponse_limitee.status_code == 429
    assert reponse_limitee.data["code"] == "trop_de_requetes"
    assert "Retry-After" in reponse_limitee


def test_schema_swagger_documente_tous_les_resultats_de_connexion():
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/v1/auth/login/"]["post"]

    assert set(operation["responses"]) == {"200", "400", "401", "405", "415", "429", "500"}
    assert operation.get("security", []) == []
