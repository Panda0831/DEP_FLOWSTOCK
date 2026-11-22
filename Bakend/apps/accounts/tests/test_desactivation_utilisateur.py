"""Vérifie la désactivation administrative d’un compte."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.core.cache import cache
from django.db import connections
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.models import JournalSecurite, TypeEvenementSecurite, Utilisateur
from apps.accounts.services import (
    DernierAdministrateurActif,
    desactiver_utilisateur_par_administrateur,
)
from apps.accounts.tests.test_creation_utilisateur import (
    CHAMPS_UTILISATEUR_ADMIN,
    client_administrateur,
)
from apps.conftest import UtilisateurFabrique

ROUTE_DESACTIVATION = "/api/v1/users/{uuid}/deactivate/"


@pytest.fixture(autouse=True)
def vider_cache_desactivation_utilisateur():
    cache.clear()


@pytest.mark.django_db
def test_admin_desactive_un_compte_revoque_ses_jetons_et_conserve_ses_donnees(
    utilisateur_vendeur,
):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique(
        email="a-desactiver@exemple.test",
        nom="Rakoto",
        prenom="Hery",
        telephone="+261320000000",
    )
    uuid_cible = cible.uuid
    hash_mot_de_passe = cible.password
    refresh_1 = RefreshToken.for_user(cible)
    refresh_2 = RefreshToken.for_user(cible)
    access = str(refresh_1.access_token)

    reponse = client.post(ROUTE_DESACTIVATION.format(uuid=uuid_cible))

    cible.refresh_from_db()
    assert reponse.status_code == 200
    assert set(reponse.data) == CHAMPS_UTILISATEUR_ADMIN
    assert reponse.data["est_actif"] is False
    assert cible.uuid == uuid_cible
    assert cible.email == "a-desactiver@exemple.test"
    assert cible.nom == "Rakoto"
    assert cible.prenom == "Hery"
    assert cible.telephone == "+261320000000"
    assert cible.password == hash_mot_de_passe
    assert not cible.is_active
    assert BlacklistedToken.objects.filter(token__user=cible).count() == 2
    with pytest.raises(TokenError):
        RefreshToken(str(refresh_1))
    with pytest.raises(TokenError):
        RefreshToken(str(refresh_2))

    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.COMPTE_DESACTIVE,
    )
    assert evenement.acteur == utilisateur_vendeur
    assert evenement.utilisateur_cible == cible
    assert evenement.succes is True
    assert evenement.details == {}
    assert "Cache-Control" in reponse
    assert reponse["Cache-Control"] == "no-store"
    assert reponse["Pragma"] == "no-cache"

    reponse_access = APIClient().get(
        "/api/v1/auth/me/",
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )
    reponse_refresh = APIClient().post(
        "/api/v1/auth/token/refresh/",
        {"refresh": str(refresh_2)},
        format="json",
    )
    reponse_connexion = APIClient().post(
        "/api/v1/auth/login/",
        {
            "email": "a-desactiver@exemple.test",
            "mot_de_passe": "Fleur!Miroir8472",
        },
        format="json",
    )
    assert reponse_access.status_code == 401
    assert reponse_access.data["code"] == "jeton_invalide"
    assert reponse_refresh.status_code == 401
    assert reponse_refresh.data["code"] == "jeton_invalide"
    assert reponse_connexion.status_code == 401
    assert reponse_connexion.data["code"] == "identifiants_invalides"


@pytest.mark.django_db
def test_administrateur_ne_peut_pas_se_desactiver_lui_meme(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.post(
        ROUTE_DESACTIVATION.format(uuid=utilisateur_vendeur.uuid),
    )

    assert reponse.status_code == 403
    assert reponse.data["code"] == "auto_desactivation_interdite"
    utilisateur_vendeur.refresh_from_db()
    assert utilisateur_vendeur.is_active
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.ACCES_REFUSE,
    )
    assert evenement.details == {"raison": "auto_desactivation_interdite"}


@pytest.mark.django_db
def test_compte_deja_inactif_retourne_409(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique(is_active=False)

    reponse = client.post(ROUTE_DESACTIVATION.format(uuid=cible.uuid))

    assert reponse.status_code == 409
    assert reponse.data["code"] == "compte_deja_desactive"


@pytest.mark.django_db
def test_vendeur_ne_peut_pas_desactiver_un_compte(utilisateur_vendeur):
    cible = UtilisateurFabrique()
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}",
    )

    reponse = client.post(ROUTE_DESACTIVATION.format(uuid=cible.uuid))

    assert reponse.status_code == 403
    assert reponse.data["code"] == "acces_interdit"
    cible.refresh_from_db()
    assert cible.is_active


@pytest.mark.django_db
def test_anonyme_ne_peut_pas_desactiver_un_compte(utilisateur_vendeur):
    reponse = APIClient().post(
        ROUTE_DESACTIVATION.format(uuid=utilisateur_vendeur.uuid),
    )

    assert reponse.status_code == 401
    assert reponse.data["code"] == "non_authentifie"


@pytest.mark.django_db
def test_uuid_inconnu_retourne_404(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.post(
        ROUTE_DESACTIVATION.format(uuid="54e091d3-76b6-49b0-a6eb-5ac9136a1019"),
    )

    assert reponse.status_code == 404
    assert reponse.data["code"] == "introuvable"


@pytest.mark.django_db
def test_service_ne_desactive_pas_le_dernier_administrateur_actif():
    administrateur = UtilisateurFabrique(
        email="dernier-admin-desactivation@exemple.test",
        role="admin",
        is_superuser=True,
    )
    acteur_non_autorise = UtilisateurFabrique(role="vendeur")

    with pytest.raises(DernierAdministrateurActif):
        desactiver_utilisateur_par_administrateur(
            administrateur.uuid,
            acteur_non_autorise,
            RequestFactory().post("/api/v1/users/deactivate/"),
        )


@pytest.mark.django_db
def test_corps_non_vide_est_refuse(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    cible = UtilisateurFabrique()

    reponse = client.post(
        ROUTE_DESACTIVATION.format(uuid=cible.uuid),
        {"est_actif": True},
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"
    cible.refresh_from_db()
    assert cible.is_active


@pytest.mark.django_db(transaction=True)
def test_deux_admins_ne_peuvent_pas_se_desactiver_mutuellement_en_parallele():
    administrateur_a = UtilisateurFabrique(
        email="desact-admin-a@exemple.test",
        role="admin",
        is_superuser=True,
    )
    administrateur_b = UtilisateurFabrique(
        email="desact-admin-b@exemple.test",
        role="admin",
        is_superuser=True,
    )
    barre = Barrier(2)

    def desactiver_acteur(uuid_cible, uuid_acteur):
        connections.close_all()
        try:
            client = APIClient()
            acteur = Utilisateur.objects.get(uuid=uuid_acteur)
            client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(acteur)}",
            )
            barre.wait(timeout=10)
            reponse = client.post(ROUTE_DESACTIVATION.format(uuid=uuid_cible))
            return reponse.status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuts = list(
            pool.map(
                lambda paires: desactiver_acteur(*paires),
                (
                    (administrateur_b.uuid, administrateur_a.uuid),
                    (administrateur_a.uuid, administrateur_b.uuid),
                ),
            )
        )

    assert statuts.count(200) == 1
    assert len(set(statuts) - {200}) == 1
    administrateur_a.refresh_from_db()
    administrateur_b.refresh_from_db()
    assert (
        sum(administrateur.is_active for administrateur in (administrateur_a, administrateur_b))
        == 1
    )
