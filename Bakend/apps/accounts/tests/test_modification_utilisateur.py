"""Vérifie la modification administrative d’un compte."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.core.cache import cache
from django.db import connections
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models import JournalSecurite, TypeEvenementSecurite, Utilisateur
from apps.accounts.services import DernierAdministrateur, modifier_utilisateur_par_administrateur
from apps.accounts.tests.test_creation_utilisateur import (
    CHAMPS_UTILISATEUR_ADMIN,
    client_administrateur,
)
from apps.conftest import UtilisateurFabrique

ROUTE_MODIFICATION = "/api/v1/users/{uuid}/"


@pytest.fixture(autouse=True)
def vider_cache_modification_utilisateur():
    cache.clear()


@pytest.mark.django_db
def test_admin_modifie_les_champs_autorises_et_journalise(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique(
        email="avant@exemple.test",
        nom="Ancien",
        prenom="Nom",
    )

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=cible.uuid),
        {
            "email": " nouveau@EXEMPLE.test ",
            "nom": "Nouveau",
            "prenom": "Prenom",
            "telephone": " +261 32.000-00-00 ",
            "role": "admin",
        },
        format="json",
    )

    cible.refresh_from_db()
    assert reponse.status_code == 200
    assert set(reponse.data) == CHAMPS_UTILISATEUR_ADMIN
    assert reponse.data["email"] == "nouveau@exemple.test"
    assert reponse.data["nom"] == "Nouveau"
    assert reponse.data["prenom"] == "Prenom"
    assert reponse.data["telephone"] == "+261320000000"
    assert reponse.data["role"] == "admin"
    assert cible.check_password("Fleur!Miroir8472")
    assert cible.est_administrateur

    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.UTILISATEUR_MODIFIE,
    )
    assert evenement.acteur == utilisateur_vendeur
    assert evenement.utilisateur_cible == cible
    assert evenement.details == {
        "champs_modifies": ["email", "nom", "prenom", "role", "telephone"],
    }
    evenement_role = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.ROLE_MODIFIE,
    )
    assert evenement_role.details == {"ancien_role": "vendeur", "nouveau_role": "admin"}


@pytest.mark.django_db
def test_modification_email_et_role_revoque_tous_les_jetons_refresh(
    utilisateur_vendeur,
):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique(email="cible@exemple.test")
    refresh_1 = RefreshToken.for_user(cible)
    refresh_2 = RefreshToken.for_user(cible)
    refresh_ids = {refresh_1["jti"], refresh_2["jti"]}

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=cible.uuid),
        {"email": "nouvelle@exemple.test"},
        format="json",
    )

    assert reponse.status_code == 200
    assert {
        jeton.jti
        for jeton in OutstandingToken.objects.filter(
            user=cible,
            blacklistedtoken__isnull=False,
        )
    } == refresh_ids
    with pytest.raises(TokenError):
        RefreshToken(str(refresh_1))
    assert BlacklistedToken.objects.filter(token__user=cible).count() == 2


@pytest.mark.django_db
def test_promotion_vers_admin_revoque_egalement_les_refresh(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique(email="vendeur@exemple.test")
    refresh = RefreshToken.for_user(cible)

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=cible.uuid),
        {"role": "admin"},
        format="json",
    )

    assert reponse.status_code == 200
    with pytest.raises(TokenError):
        RefreshToken(str(refresh))


@pytest.mark.django_db
def test_admin_ne_peut_pas_modifier_son_propre_role(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=utilisateur_vendeur.uuid),
        {"role": "vendeur"},
        format="json",
    )

    assert reponse.status_code == 403
    assert reponse.data["code"] == "auto_modification_role_interdite"
    utilisateur_vendeur.refresh_from_db()
    assert utilisateur_vendeur.role == "admin"


@pytest.mark.django_db
def test_email_deja_utilise_est_refuse_sans_modifier_le_compte(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique(email="cible@exemple.test", nom="Ancien")
    UtilisateurFabrique(email="pris@exemple.test")

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=cible.uuid),
        {"email": "PRIS@exemple.test"},
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"
    cible.refresh_from_db()
    assert cible.email == "cible@exemple.test"
    assert cible.nom == "Ancien"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "champ",
    ["password", "mot_de_passe", "est_actif", "is_active", "is_superuser", "uuid", "id"],
)
def test_champs_interdits_sont_refuses(champ, utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique()

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=cible.uuid),
        {champ: "valeur"},
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "champs_inconnus"
    cible.refresh_from_db()
    assert cible.role == "vendeur"
    assert cible.is_active is True


@pytest.mark.django_db
def test_corps_vide_ne_modifie_pas_le_compte_et_ne_journalise_pas(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique()
    date_modification = cible.date_modification
    nombre_evenements = JournalSecurite.objects.count()

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=cible.uuid),
        {},
        format="json",
    )

    cible.refresh_from_db()
    assert reponse.status_code == 200
    assert cible.date_modification == date_modification
    assert JournalSecurite.objects.count() == nombre_evenements


@pytest.mark.django_db
def test_vendeur_est_interdit_de_modifier_un_utilisateur(utilisateur_vendeur):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
    )

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=utilisateur_vendeur.uuid),
        {"nom": "Interdit"},
        format="json",
    )

    assert reponse.status_code == 403
    assert reponse.data["code"] == "acces_interdit"


@pytest.mark.django_db
def test_anonyme_est_refuse(utilisateur_vendeur):
    reponse = APIClient().patch(
        ROUTE_MODIFICATION.format(uuid=utilisateur_vendeur.uuid),
        {"nom": "Interdit"},
        format="json",
    )

    assert reponse.status_code == 401
    assert reponse.data["code"] == "non_authentifie"


@pytest.mark.django_db
def test_uuid_inexistant_retourne_404(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=uuid.uuid4()),
        {"nom": "Inexistant"},
        format="json",
    )

    assert reponse.status_code == 404
    assert reponse.data["code"] == "introuvable"


@pytest.mark.django_db
def test_put_est_interdit(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.put(
        ROUTE_MODIFICATION.format(uuid=utilisateur_vendeur.uuid),
        {"nom": "Interdit"},
        format="json",
    )

    assert reponse.status_code == 405
    assert reponse.data["code"] == "methode_non_autorisee"


@pytest.mark.django_db
def test_limite_de_debit_documentee(utilisateur_vendeur, monkeypatch):
    client = client_administrateur(utilisateur_vendeur)
    monkeypatch.setattr(
        UserRateThrottle,
        "allow_request",
        lambda throttle, requete, vue: False,
    )
    monkeypatch.setattr(UserRateThrottle, "wait", lambda throttle: 60)

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=utilisateur_vendeur.uuid),
        {"nom": "Interdit"},
        format="json",
    )

    assert reponse.status_code == 429
    assert reponse["Retry-After"] == "60"


@pytest.mark.django_db
def test_service_ne_retrograde_pas_le_dernier_administrateur_actif():
    administrateur = UtilisateurFabrique(
        email="dernier-admin@exemple.test",
        role="admin",
        is_superuser=True,
    )
    acteur_non_autorise = UtilisateurFabrique(role="vendeur")

    with pytest.raises(DernierAdministrateur):
        modifier_utilisateur_par_administrateur(
            administrateur.uuid,
            {"role": "vendeur"},
            acteur_non_autorise,
            RequestFactory().patch("/api/v1/users/"),
        )


@pytest.mark.django_db
def test_erreur_interne_est_normalisee_et_sans_detail(utilisateur_vendeur, monkeypatch):
    client = client_administrateur(utilisateur_vendeur)

    def provoquer_erreur(*args, **kwargs):
        raise RuntimeError("secret technique")

    monkeypatch.setattr(
        "apps.accounts.services.Utilisateur.objects.select_for_update",
        provoquer_erreur,
    )

    reponse = client.patch(
        ROUTE_MODIFICATION.format(uuid=uuid.uuid4()),
        {"nom": "Interdit"},
        format="json",
    )

    assert reponse.status_code == 500
    assert reponse.data == {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    }
    assert "secret technique" not in str(reponse.data)


@pytest.mark.django_db(transaction=True)
def test_deux_admins_ne_peuvent_pas_se_retrograder_simultanement():
    administrateur_a = UtilisateurFabrique(
        email="admin-a@exemple.test",
        role="admin",
        is_superuser=True,
    )
    administrateur_b = UtilisateurFabrique(
        email="admin-b@exemple.test",
        role="admin",
        is_superuser=True,
    )
    barre = Barrier(2)

    def retrograder_acteur(uuid_cible, uuid_acteur):
        connections.close_all()
        try:
            acteur = Utilisateur.objects.get(uuid=uuid_acteur)
            barre.wait(timeout=10)
            modifier_utilisateur_par_administrateur(
                uuid_cible,
                {"role": "vendeur"},
                acteur,
                RequestFactory().patch("/api/v1/users/"),
            )
            return "modifie"
        except Exception as erreur:
            return erreur.get_codes() if hasattr(erreur, "get_codes") else type(erreur).__name__
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        resultats = list(
            pool.map(
                lambda paires: retrograder_acteur(*paires),
                (
                    (administrateur_b.uuid, administrateur_a.uuid),
                    (administrateur_a.uuid, administrateur_b.uuid),
                ),
            )
        )

    assert resultats.count("modifie") == 1
    assert len(set(resultats) - {"modifie"}) == 1
    administrateur_a.refresh_from_db()
    administrateur_b.refresh_from_db()
    assert (
        sum(
            administrateur.role == "admin"
            for administrateur in (administrateur_a, administrateur_b)
        )
        == 1
    )
