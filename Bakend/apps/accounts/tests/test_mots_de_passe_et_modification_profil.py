"""Vérifie les endpoints de mot de passe et de modification du profil."""

from urllib.parse import parse_qs, urlparse

import pytest
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from freezegun import freeze_time
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.exemples_json import (
    EXEMPLES_JSON_CHANGEMENT_MOT_DE_PASSE,
    EXEMPLES_JSON_CONFIRMATION_REINITIALISATION,
    EXEMPLES_JSON_DEMANDE_REINITIALISATION,
    EXEMPLES_JSON_MODIFICATION_PROFIL,
)
from apps.accounts.models import JournalSecurite, TypeEvenementSecurite
from apps.accounts.tests.test_contrat_reponses_json import verifier_forme_json
from apps.accounts.views import mots_de_passe as views_mots_de_passe
from apps.accounts.views import profil as views_profil

ROUTE_CHANGEMENT_MOT_DE_PASSE = "/api/v1/auth/password/change/"
ROUTE_DEMANDE_REINITIALISATION = "/api/v1/auth/password/reset/request/"
ROUTE_CONFIRMATION_REINITIALISATION = "/api/v1/auth/password/reset/confirm/"
ROUTE_PROFIL = "/api/v1/auth/me/"
ANCIEN_MOT_DE_PASSE = "Fleur!Miroir8472"
NOUVEAU_MOT_DE_PASSE = "Givre!Atlas5981"


@pytest.fixture(autouse=True)
def vider_cache():
    cache.clear()


def client_authentifie(utilisateur):
    client = APIClient()
    jeton = str(RefreshToken.for_user(utilisateur).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jeton}")
    return client


def donnees_changement_mot_de_passe(
    ancien=ANCIEN_MOT_DE_PASSE,
    nouveau=NOUVEAU_MOT_DE_PASSE,
    confirmation=NOUVEAU_MOT_DE_PASSE,
):
    return {
        "ancien_mot_de_passe": ancien,
        "nouveau_mot_de_passe": nouveau,
        "confirmation_nouveau_mot_de_passe": confirmation,
    }


@pytest.mark.django_db
def test_changement_mot_de_passe_revoque_les_sessions_et_leve_le_blocage(utilisateur_vendeur):
    utilisateur_vendeur.doit_changer_mot_de_passe = True
    utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])
    ancien_jeton = RefreshToken.for_user(utilisateur_vendeur)
    client = client_authentifie(utilisateur_vendeur)

    reponse = client.post(
        ROUTE_CHANGEMENT_MOT_DE_PASSE,
        donnees_changement_mot_de_passe(),
        format="json",
    )

    utilisateur_vendeur.refresh_from_db()
    entree_jeton = OutstandingToken.objects.get(jti=ancien_jeton["jti"])
    assert reponse.status_code == 200
    assert reponse.data == {"detail": "Mot de passe modifié. Veuillez vous reconnecter."}
    assert utilisateur_vendeur.check_password(NOUVEAU_MOT_DE_PASSE)
    assert not utilisateur_vendeur.doit_changer_mot_de_passe
    assert utilisateur_vendeur.date_dernier_changement_mot_de_passe is not None
    assert BlacklistedToken.objects.filter(token=entree_jeton).exists()
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.MOT_DE_PASSE_CHANGE,
        utilisateur_cible=utilisateur_vendeur,
    ).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("donnees", "code", "champ"),
    [
        (
            donnees_changement_mot_de_passe(ancien="MauvaisMotDePasse!"),
            "ancien_mot_de_passe_incorrect",
            None,
        ),
        (
            donnees_changement_mot_de_passe(confirmation="AutreMotDePasse!2026"),
            "donnees_invalides",
            "confirmation_nouveau_mot_de_passe",
        ),
        (
            donnees_changement_mot_de_passe(
                nouveau=ANCIEN_MOT_DE_PASSE,
                confirmation=ANCIEN_MOT_DE_PASSE,
            ),
            "donnees_invalides",
            "nouveau_mot_de_passe",
        ),
        (
            donnees_changement_mot_de_passe(nouveau="court", confirmation="court"),
            "donnees_invalides",
            "nouveau_mot_de_passe",
        ),
    ],
)
def test_changement_refuse_les_donnees_invalides(utilisateur_vendeur, donnees, code, champ):
    reponse = client_authentifie(utilisateur_vendeur).post(
        ROUTE_CHANGEMENT_MOT_DE_PASSE,
        donnees,
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == code
    if champ is not None:
        assert champ in reponse.data["erreurs"]
    utilisateur_vendeur.refresh_from_db()
    assert utilisateur_vendeur.check_password(ANCIEN_MOT_DE_PASSE)


@pytest.mark.django_db
def test_changement_refuse_les_champs_inconnus_sans_effet(utilisateur_vendeur):
    donnees = donnees_changement_mot_de_passe() | {"role": "admin"}

    reponse = client_authentifie(utilisateur_vendeur).post(
        ROUTE_CHANGEMENT_MOT_DE_PASSE,
        donnees,
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "champs_inconnus"
    utilisateur_vendeur.refresh_from_db()
    assert utilisateur_vendeur.role == "vendeur"
    assert utilisateur_vendeur.check_password(ANCIEN_MOT_DE_PASSE)


@pytest.mark.django_db
def test_changement_refuse_un_utilisateur_anonyme():
    reponse = APIClient().post(
        ROUTE_CHANGEMENT_MOT_DE_PASSE,
        donnees_changement_mot_de_passe(),
        format="json",
    )

    assert reponse.status_code == 401
    assert reponse.data["code"] == "non_authentifie"


def executer_threads_synchrones(monkeypatch):
    from apps.accounts import services

    class ThreadSynchrone:
        def __init__(self, target, args, daemon):
            self.target = target
            self.args = args
            self.daemon = daemon

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(services, "Thread", ThreadSynchrone)


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    URL_FRONTEND_REINITIALISATION="https://app.exemple.test/reinitialiser",
)
def test_demande_reinitialisation_envoie_le_lien_uniquement_au_compte_actif(
    utilisateur_vendeur,
    monkeypatch,
):
    executer_threads_synchrones(monkeypatch)

    reponse_compte_actif = APIClient().post(
        ROUTE_DEMANDE_REINITIALISATION,
        {"email": utilisateur_vendeur.email},
        format="json",
    )
    reponse_compte_inconnu = APIClient().post(
        ROUTE_DEMANDE_REINITIALISATION,
        {"email": "inconnu@exemple.test"},
        format="json",
    )

    assert reponse_compte_actif.status_code == 200
    assert reponse_compte_actif.data == reponse_compte_inconnu.data
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [utilisateur_vendeur.email]
    lien = next(
        ligne
        for ligne in mail.outbox[0].body.splitlines()
        if ligne.startswith("https://app.exemple.test/")
    )
    query = parse_qs(urlparse(lien).query)
    assert query["uid"] == [str(utilisateur_vendeur.uuid)]
    assert query["token"]
    confirmation = APIClient().post(
        ROUTE_CONFIRMATION_REINITIALISATION,
        {
            "uid": query["uid"][0],
            "token": query["token"][0],
            "nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
            "confirmation_nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
        },
        format="json",
    )
    assert confirmation.status_code == 200
    utilisateur_vendeur.is_active = False
    utilisateur_vendeur.save(update_fields=["is_active"])
    reponse_compte_inactif = APIClient().post(
        ROUTE_DEMANDE_REINITIALISATION,
        {"email": utilisateur_vendeur.email},
        format="json",
    )
    assert reponse_compte_actif.data == reponse_compte_inactif.data
    assert query["token"][0] not in repr(
        JournalSecurite.objects.filter(
            type_evenement=TypeEvenementSecurite.REINITIALISATION_DEMANDEE
        ).values("details")
    )


@pytest.mark.django_db
def test_demande_reinitialisation_refuse_email_invalide():
    reponse = APIClient().post(
        ROUTE_DEMANDE_REINITIALISATION,
        {"email": "adresse-invalide"},
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"


@pytest.mark.django_db
def test_confirmation_reinitialisation_change_le_mot_de_passe_une_seule_fois(
    utilisateur_vendeur,
):
    ancien_jeton = RefreshToken.for_user(utilisateur_vendeur)
    jeton_reinitialisation = PasswordResetTokenGenerator().make_token(utilisateur_vendeur)
    donnees = {
        "uid": str(utilisateur_vendeur.uuid),
        "token": jeton_reinitialisation,
        "nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
        "confirmation_nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
    }

    reponse = APIClient().post(
        ROUTE_CONFIRMATION_REINITIALISATION,
        donnees,
        format="json",
    )

    utilisateur_vendeur.refresh_from_db()
    entree_jeton = OutstandingToken.objects.get(jti=ancien_jeton["jti"])
    assert reponse.status_code == 200
    assert utilisateur_vendeur.check_password(NOUVEAU_MOT_DE_PASSE)
    assert not utilisateur_vendeur.doit_changer_mot_de_passe
    assert BlacklistedToken.objects.filter(token=entree_jeton).exists()
    assert APIClient().post(
        ROUTE_CONFIRMATION_REINITIALISATION,
        donnees,
        format="json",
    ).data == {
        "detail": "Lien de réinitialisation invalide ou expiré.",
        "code": "jeton_invalide",
    }


@pytest.mark.django_db
@pytest.mark.parametrize("uid", ["00000000-0000-0000-0000-000000000000"])
def test_confirmation_reinitialisation_uniformise_uid_inconnu(utilisateur_vendeur, uid):
    donnees = {
        "uid": uid,
        "token": PasswordResetTokenGenerator().make_token(utilisateur_vendeur),
        "nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
        "confirmation_nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
    }

    reponse = APIClient().post(ROUTE_CONFIRMATION_REINITIALISATION, donnees, format="json")

    assert reponse.status_code == 400
    assert reponse.data == {
        "detail": "Lien de réinitialisation invalide ou expiré.",
        "code": "jeton_invalide",
    }


@pytest.mark.django_db
@pytest.mark.parametrize("motif", ["jeton_falsifie", "compte_inactif", "jeton_expire"])
def test_confirmation_reinitialisation_uniformise_les_liens_invalides(
    utilisateur_vendeur,
    motif,
):
    with freeze_time("2026-01-01T00:00:00Z"):
        jeton = PasswordResetTokenGenerator().make_token(utilisateur_vendeur)
    if motif == "jeton_falsifie":
        jeton = f"{jeton}falsifie"
    elif motif == "compte_inactif":
        utilisateur_vendeur.is_active = False
        utilisateur_vendeur.save(update_fields=["is_active"])

    donnees = {
        "uid": str(utilisateur_vendeur.uuid),
        "token": jeton,
        "nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
        "confirmation_nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
    }
    instant = "2026-01-01T01:01:00Z" if motif == "jeton_expire" else "2026-01-01T00:01:00Z"
    with freeze_time(instant):
        reponse = APIClient().post(
            ROUTE_CONFIRMATION_REINITIALISATION,
            donnees,
            format="json",
        )

    assert reponse.status_code == 400
    assert reponse.data == {
        "detail": "Lien de réinitialisation invalide ou expiré.",
        "code": "jeton_invalide",
    }


@pytest.mark.django_db
def test_confirmation_reinitialisation_refuse_un_mot_de_passe_faible(utilisateur_vendeur):
    donnees = {
        "uid": str(utilisateur_vendeur.uuid),
        "token": PasswordResetTokenGenerator().make_token(utilisateur_vendeur),
        "nouveau_mot_de_passe": "court",
        "confirmation_nouveau_mot_de_passe": "court",
    }

    reponse = APIClient().post(ROUTE_CONFIRMATION_REINITIALISATION, donnees, format="json")

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"
    assert "nouveau_mot_de_passe" in reponse.data["erreurs"]


@pytest.mark.django_db
def test_changement_mot_de_passe_est_limite_par_compte(utilisateur_vendeur):
    limites = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] | {
        "changement_mot_de_passe": "1/min",
    }
    configuration = settings.REST_FRAMEWORK | {"DEFAULT_THROTTLE_RATES": limites}
    client = client_authentifie(utilisateur_vendeur)
    with override_settings(REST_FRAMEWORK=configuration):
        premiere_reponse = client.post(
            ROUTE_CHANGEMENT_MOT_DE_PASSE,
            donnees_changement_mot_de_passe(),
            format="json",
        )
        seconde_reponse = client.post(
            ROUTE_CHANGEMENT_MOT_DE_PASSE,
            donnees_changement_mot_de_passe(
                ancien=NOUVEAU_MOT_DE_PASSE,
                nouveau="Soleil!Rivage5038",
                confirmation="Soleil!Rivage5038",
            ),
            format="json",
        )

    assert premiere_reponse.status_code == 200
    assert seconde_reponse.status_code == 429
    assert int(seconde_reponse["Retry-After"]) > 0
    verifier_forme_json(
        seconde_reponse,
        EXEMPLES_JSON_CHANGEMENT_MOT_DE_PASSE["changement_limite_atteinte"],
    )


@pytest.mark.django_db
def test_demande_reinitialisation_est_limitee_par_ip_et_email():
    limites = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] | {
        "reinitialisation_demande": "5/min",
        "reinitialisation_demande_par_email": "1/min",
    }
    configuration = settings.REST_FRAMEWORK | {"DEFAULT_THROTTLE_RATES": limites}
    client = APIClient()
    donnees = {"email": "inconnu@exemple.test"}
    with override_settings(REST_FRAMEWORK=configuration):
        premiere_reponse = client.post(
            ROUTE_DEMANDE_REINITIALISATION,
            donnees,
            format="json",
        )
        seconde_reponse = client.post(
            ROUTE_DEMANDE_REINITIALISATION,
            donnees,
            format="json",
        )

    assert premiere_reponse.status_code == 200
    assert seconde_reponse.status_code == 429
    assert int(seconde_reponse["Retry-After"]) > 0
    verifier_forme_json(
        seconde_reponse,
        EXEMPLES_JSON_DEMANDE_REINITIALISATION["demande_reinitialisation_limite_atteinte"],
    )


@pytest.mark.django_db
def test_confirmation_reinitialisation_est_limitee_par_ip(utilisateur_vendeur):
    limites = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] | {
        "reinitialisation_confirmation": "1/min",
    }
    configuration = settings.REST_FRAMEWORK | {"DEFAULT_THROTTLE_RATES": limites}
    donnees = {
        "uid": str(utilisateur_vendeur.uuid),
        "token": "jeton-invalide",
        "nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
        "confirmation_nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
    }
    with override_settings(REST_FRAMEWORK=configuration):
        premiere_reponse = APIClient().post(
            ROUTE_CONFIRMATION_REINITIALISATION,
            donnees,
            format="json",
        )
        seconde_reponse = APIClient().post(
            ROUTE_CONFIRMATION_REINITIALISATION,
            donnees,
            format="json",
        )

    assert premiere_reponse.status_code == 400
    assert seconde_reponse.status_code == 429
    assert int(seconde_reponse["Retry-After"]) > 0
    verifier_forme_json(
        seconde_reponse,
        EXEMPLES_JSON_CONFIRMATION_REINITIALISATION[
            "confirmation_reinitialisation_limite_atteinte"
        ],
    )


@pytest.mark.django_db
def test_modification_profil_change_uniquement_les_champs_autorises(utilisateur_vendeur):
    reponse = client_authentifie(utilisateur_vendeur).patch(
        ROUTE_PROFIL,
        {"nom": "Randria", "telephone": "+261320000000"},
        format="json",
    )

    utilisateur_vendeur.refresh_from_db()
    assert reponse.status_code == 200
    assert reponse.data["nom"] == "Randria"
    assert reponse.data["telephone"] == "+261320000000"
    assert utilisateur_vendeur.nom == "Randria"
    assert JournalSecurite.objects.filter(
        type_evenement=TypeEvenementSecurite.PROFIL_MODIFIE,
        utilisateur_cible=utilisateur_vendeur,
    ).exists()


@pytest.mark.django_db
def test_modification_profil_refuse_un_telephone_invalide(utilisateur_vendeur):
    reponse = client_authentifie(utilisateur_vendeur).patch(
        ROUTE_PROFIL,
        {"telephone": "pas-un-numero"},
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"
    assert "telephone" in reponse.data["erreurs"]


@pytest.mark.django_db
def test_modification_profil_refuse_un_utilisateur_anonyme():
    reponse = APIClient().patch(
        ROUTE_PROFIL,
        {"nom": "Randria"},
        format="json",
    )

    assert reponse.status_code == 401
    assert reponse.data["code"] == "non_authentifie"


@pytest.mark.django_db
@pytest.mark.parametrize("champ", ["role", "email", "est_actif", "is_superuser"])
def test_modification_profil_refuse_les_champs_non_autorises(utilisateur_vendeur, champ):
    reponse = client_authentifie(utilisateur_vendeur).patch(
        ROUTE_PROFIL,
        {champ: "admin"},
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "champs_inconnus"
    utilisateur_vendeur.refresh_from_db()
    assert utilisateur_vendeur.role == "vendeur"


@pytest.mark.django_db
def test_modification_profil_est_bloquee_si_un_changement_de_mot_de_passe_est_requis(
    utilisateur_vendeur,
):
    utilisateur_vendeur.doit_changer_mot_de_passe = True
    utilisateur_vendeur.save(update_fields=["doit_changer_mot_de_passe"])

    reponse = client_authentifie(utilisateur_vendeur).patch(
        ROUTE_PROFIL,
        {"nom": "Randria"},
        format="json",
    )

    assert reponse.status_code == 403
    assert reponse.data["code"] == "changement_mot_de_passe_requis"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("operation", "exemple"),
    [
        ("changement", "changement_erreur_interne"),
        ("demande", "demande_reinitialisation_erreur_interne"),
        ("confirmation", "confirmation_reinitialisation_erreur_interne"),
        ("profil", "profil_modification_erreur_interne"),
    ],
)
def test_erreur_interne_ne_revele_aucun_detail(
    utilisateur_vendeur,
    monkeypatch,
    operation,
    exemple,
):
    def echouer(*args, **kwargs):
        raise RuntimeError("secret technique")

    client = APIClient()
    if operation == "changement":
        monkeypatch.setattr(views_mots_de_passe, "changer_mot_de_passe_utilisateur", echouer)
        client = client_authentifie(utilisateur_vendeur)
        reponse = client.post(
            ROUTE_CHANGEMENT_MOT_DE_PASSE,
            donnees_changement_mot_de_passe(),
            format="json",
        )
        reference = EXEMPLES_JSON_CHANGEMENT_MOT_DE_PASSE[exemple]
    elif operation == "demande":
        monkeypatch.setattr(
            views_mots_de_passe,
            "demander_reinitialisation_mot_de_passe",
            echouer,
        )
        reponse = client.post(
            ROUTE_DEMANDE_REINITIALISATION,
            {"email": "inconnu@exemple.test"},
            format="json",
        )
        reference = EXEMPLES_JSON_DEMANDE_REINITIALISATION[exemple]
    elif operation == "confirmation":
        monkeypatch.setattr(
            views_mots_de_passe,
            "confirmer_reinitialisation_mot_de_passe",
            echouer,
        )
        reponse = client.post(
            ROUTE_CONFIRMATION_REINITIALISATION,
            {
                "uid": str(utilisateur_vendeur.uuid),
                "token": "jeton",
                "nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
                "confirmation_nouveau_mot_de_passe": NOUVEAU_MOT_DE_PASSE,
            },
            format="json",
        )
        reference = EXEMPLES_JSON_CONFIRMATION_REINITIALISATION[exemple]
    else:
        monkeypatch.setattr(views_profil, "modifier_profil_utilisateur", echouer)
        client = client_authentifie(utilisateur_vendeur)
        reponse = client.patch(ROUTE_PROFIL, {"nom": "Randria"}, format="json")
        reference = EXEMPLES_JSON_MODIFICATION_PROFIL[exemple]

    assert reponse.status_code == 500
    assert "secret technique" not in str(reponse.data)
    verifier_forme_json(reponse, reference)
