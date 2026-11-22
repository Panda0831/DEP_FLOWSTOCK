"""Vérifie chaque sortie documentée des endpoints 10 à 13."""

import pytest
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.exemples_json import (
    EXEMPLES_JSON_CHANGEMENT_MOT_DE_PASSE,
    EXEMPLES_JSON_CONFIRMATION_REINITIALISATION,
    EXEMPLES_JSON_DEMANDE_REINITIALISATION,
    EXEMPLES_JSON_MODIFICATION_PROFIL,
)
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.tests.test_mots_de_passe_et_modification_profil import (
    ANCIEN_MOT_DE_PASSE,
    NOUVEAU_MOT_DE_PASSE,
    ROUTE_CHANGEMENT_MOT_DE_PASSE,
    ROUTE_CONFIRMATION_REINITIALISATION,
    ROUTE_DEMANDE_REINITIALISATION,
    ROUTE_PROFIL,
    client_authentifie,
    donnees_changement_mot_de_passe,
)


@pytest.fixture(autouse=True)
def vider_cache():
    cache.clear()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("cas", "statut"),
    [
        ("changement_succes", 200),
        ("changement_ancien_incorrect", 400),
        ("changement_validation", 400),
        ("changement_confirmation_invalide", 400),
        ("changement_mot_de_passe_identique", 400),
        ("changement_champs_inconnus", 400),
        ("changement_json_malforme", 400),
        ("changement_non_authentifie", 401),
        ("changement_jeton_invalide", 401),
        ("changement_jeton_expire", 401),
        ("changement_methode_interdite", 405),
        ("changement_type_contenu", 415),
    ],
)
def test_contrat_json_changement_mot_de_passe(
    cas,
    statut,
    utilisateur_vendeur,
):
    client = APIClient()
    donnees = donnees_changement_mot_de_passe()

    if cas == "changement_non_authentifie":
        reponse = client.post(ROUTE_CHANGEMENT_MOT_DE_PASSE, donnees, format="json")
    else:
        client = client_authentifie(utilisateur_vendeur)
        if cas == "changement_ancien_incorrect":
            donnees["ancien_mot_de_passe"] = "MauvaisMotDePasse!"
        elif cas == "changement_validation":
            donnees["nouveau_mot_de_passe"] = donnees["confirmation_nouveau_mot_de_passe"] = "court"
        elif cas == "changement_confirmation_invalide":
            donnees["confirmation_nouveau_mot_de_passe"] = "AutreMotDePasse!2026"
        elif cas == "changement_mot_de_passe_identique":
            donnees["nouveau_mot_de_passe"] = ANCIEN_MOT_DE_PASSE
            donnees["confirmation_nouveau_mot_de_passe"] = ANCIEN_MOT_DE_PASSE
        elif cas == "changement_champs_inconnus":
            donnees["role"] = "admin"

        if cas == "changement_json_malforme":
            reponse = client.generic(
                "POST",
                ROUTE_CHANGEMENT_MOT_DE_PASSE,
                data=b"{",
                content_type="application/json",
            )
        elif cas == "changement_type_contenu":
            reponse = client.generic(
                "POST",
                ROUTE_CHANGEMENT_MOT_DE_PASSE,
                data=b"corps",
                content_type="text/plain",
            )
        elif cas == "changement_methode_interdite":
            reponse = client.get(ROUTE_CHANGEMENT_MOT_DE_PASSE)
        elif cas == "changement_jeton_invalide":
            client.credentials(HTTP_AUTHORIZATION="Bearer jeton-invalide")
            reponse = client.post(ROUTE_CHANGEMENT_MOT_DE_PASSE, donnees, format="json")
        elif cas == "changement_jeton_expire":
            with freeze_time("2026-01-01T00:00:00Z"):
                jeton = str(AccessToken.for_user(utilisateur_vendeur))
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
            with freeze_time("2026-01-01T00:16:00Z"):
                reponse = client.post(
                    ROUTE_CHANGEMENT_MOT_DE_PASSE,
                    donnees,
                    format="json",
                )
        else:
            reponse = client.post(ROUTE_CHANGEMENT_MOT_DE_PASSE, donnees, format="json")

    assert reponse.status_code == statut
    verifier_forme_json(reponse, EXEMPLES_JSON_CHANGEMENT_MOT_DE_PASSE[cas])


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("cas", "statut"),
    [
        ("demande_reinitialisation_succes", 200),
        ("demande_reinitialisation_email_invalide", 400),
        ("demande_reinitialisation_champs_inconnus", 400),
        ("demande_reinitialisation_json_malforme", 400),
        ("demande_reinitialisation_type_contenu", 415),
        ("demande_reinitialisation_methode_interdite", 405),
    ],
)
def test_contrat_json_demande_reinitialisation(cas, statut):
    client = APIClient()
    donnees = {"email": "inconnu@exemple.test"}
    if cas == "demande_reinitialisation_email_invalide":
        donnees["email"] = "adresse-invalide"
    elif cas == "demande_reinitialisation_champs_inconnus":
        donnees["role"] = "admin"

    if cas == "demande_reinitialisation_json_malforme":
        reponse = client.generic(
            "POST",
            ROUTE_DEMANDE_REINITIALISATION,
            data=b"{",
            content_type="application/json",
        )
    elif cas == "demande_reinitialisation_type_contenu":
        reponse = client.generic(
            "POST",
            ROUTE_DEMANDE_REINITIALISATION,
            data=b"corps",
            content_type="text/plain",
        )
    elif cas == "demande_reinitialisation_methode_interdite":
        reponse = client.get(ROUTE_DEMANDE_REINITIALISATION)
    else:
        reponse = client.post(ROUTE_DEMANDE_REINITIALISATION, donnees, format="json")

    assert reponse.status_code == statut
    verifier_forme_json(reponse, EXEMPLES_JSON_DEMANDE_REINITIALISATION[cas])


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("cas", "statut"),
    [
        ("confirmation_reinitialisation_succes", 200),
        ("confirmation_reinitialisation_jeton_invalide", 400),
        ("confirmation_reinitialisation_validation", 400),
        ("confirmation_reinitialisation_confirmation_invalide", 400),
        ("confirmation_reinitialisation_champs_inconnus", 400),
        ("confirmation_reinitialisation_json_malforme", 400),
        ("confirmation_reinitialisation_type_contenu", 415),
        ("confirmation_reinitialisation_methode_interdite", 405),
    ],
)
def test_contrat_json_confirmation_reinitialisation(
    cas,
    statut,
    utilisateur_vendeur,
):
    donnees = {
        "uid": str(utilisateur_vendeur.uuid),
        "token": PasswordResetTokenGenerator().make_token(utilisateur_vendeur),
        "nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
        "confirmation_nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
    }
    if cas == "confirmation_reinitialisation_jeton_invalide":
        donnees["token"] = "jeton-falsifie"
    elif cas == "confirmation_reinitialisation_validation":
        donnees["nouveau_mot_de_passe"] = "court"
        donnees["confirmation_nouveau_mot_de_passe"] = "court"
    elif cas == "confirmation_reinitialisation_confirmation_invalide":
        donnees["confirmation_nouveau_mot_de_passe"] = "AutreMotDePasse!2026"
    elif cas == "confirmation_reinitialisation_champs_inconnus":
        donnees["role"] = "admin"

    client = APIClient()
    if cas == "confirmation_reinitialisation_json_malforme":
        reponse = client.generic(
            "POST",
            ROUTE_CONFIRMATION_REINITIALISATION,
            data=b"{",
            content_type="application/json",
        )
    elif cas == "confirmation_reinitialisation_type_contenu":
        reponse = client.generic(
            "POST",
            ROUTE_CONFIRMATION_REINITIALISATION,
            data=b"corps",
            content_type="text/plain",
        )
    elif cas == "confirmation_reinitialisation_methode_interdite":
        reponse = client.get(ROUTE_CONFIRMATION_REINITIALISATION)
    else:
        reponse = client.post(
            ROUTE_CONFIRMATION_REINITIALISATION,
            donnees,
            format="json",
        )

    assert reponse.status_code == statut
    verifier_forme_json(reponse, EXEMPLES_JSON_CONFIRMATION_REINITIALISATION[cas])


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("cas", "statut"),
    [
        ("profil_modification_succes", 200),
        ("profil_modification_validation", 400),
        ("profil_modification_champs_inconnus", 400),
        ("profil_modification_json_malforme", 400),
        ("profil_modification_type_contenu", 415),
        ("profil_modification_non_authentifie", 401),
        ("profil_modification_jeton_invalide", 401),
        ("profil_modification_jeton_expire", 401),
        ("profil_modification_changement_mot_de_passe_requis", 403),
        ("profil_modification_methode_interdite", 405),
    ],
)
def test_contrat_json_modification_profil(cas, statut, utilisateur_vendeur):
    client = APIClient()
    donnees = {"nom": "Randria"}

    if cas == "profil_modification_succes":
        utilisateur_vendeur.telephone = "+261320000000"
        utilisateur_vendeur.last_login = timezone.now()
        utilisateur_vendeur.save(update_fields=["telephone", "last_login"])
        donnees = {"nom": "Rakoto"}

    if cas == "profil_modification_non_authentifie":
        reponse = client.patch(ROUTE_PROFIL, donnees, format="json")
    else:
        if cas == "profil_modification_validation":
            donnees = {"telephone": "pas-un-numero"}
        elif cas == "profil_modification_champs_inconnus":
            donnees = {"role": "admin"}
        elif cas == "profil_modification_json_malforme":
            donnees = None
        elif cas == "profil_modification_type_contenu":
            donnees = None
        elif cas == "profil_modification_changement_mot_de_passe_requis":
            utilisateur_vendeur.doit_changer_mot_de_passe = True
            utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])

        client = client_authentifie(utilisateur_vendeur)
        if cas == "profil_modification_json_malforme":
            reponse = client.generic(
                "PATCH",
                ROUTE_PROFIL,
                data=b"{",
                content_type="application/json",
            )
        elif cas == "profil_modification_type_contenu":
            reponse = client.generic(
                "PATCH",
                ROUTE_PROFIL,
                data=b"corps",
                content_type="text/plain",
            )
        elif cas == "profil_modification_jeton_invalide":
            client.credentials(HTTP_AUTHORIZATION="Bearer jeton-invalide")
            reponse = client.patch(ROUTE_PROFIL, {"nom": "Randria"}, format="json")
        elif cas == "profil_modification_jeton_expire":
            with freeze_time("2026-01-01T00:00:00Z"):
                jeton = str(AccessToken.for_user(utilisateur_vendeur))
            client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
            with freeze_time("2026-01-01T00:16:00Z"):
                reponse = client.patch(ROUTE_PROFIL, {"nom": "Randria"}, format="json")
        elif cas == "profil_modification_methode_interdite":
            reponse = client.post(ROUTE_PROFIL, {}, format="json")
        else:
            reponse = client.patch(ROUTE_PROFIL, donnees, format="json")

    assert reponse.status_code == statut
    verifier_forme_json(reponse, EXEMPLES_JSON_MODIFICATION_PROFIL[cas])


@pytest.mark.django_db
def test_modification_profil_est_limitee_par_utilisateur(utilisateur_vendeur):
    limites = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] | {"user": "1/min"}
    configuration = settings.REST_FRAMEWORK | {"DEFAULT_THROTTLE_RATES": limites}
    client = client_authentifie(utilisateur_vendeur)
    with override_settings(REST_FRAMEWORK=configuration):
        premiere_reponse = client.patch(
            ROUTE_PROFIL,
            {"nom": "Randria"},
            format="json",
        )
        seconde_reponse = client.patch(
            ROUTE_PROFIL,
            {"nom": "Rakoto"},
            format="json",
        )

    assert premiere_reponse.status_code == 200
    assert seconde_reponse.status_code == 429
    assert int(seconde_reponse["Retry-After"]) > 0
    verifier_forme_json(
        seconde_reponse,
        EXEMPLES_JSON_MODIFICATION_PROFIL["profil_modification_limite_atteinte"],
    )
