"""Vérifie la consultation paginée et filtrée des utilisateurs."""

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import JournalSecurite, TypeEvenementSecurite
from apps.accounts.tests.test_creation_utilisateur import (
    CHAMPS_UTILISATEUR_ADMIN,
    client_administrateur,
)
from apps.conftest import UtilisateurFabrique

ROUTE_UTILISATEURS = "/api/v1/users/"


@pytest.fixture(autouse=True)
def vider_cache_liste_utilisateurs():
    cache.clear()


@pytest.mark.django_db
def test_admin_obtient_une_liste_paginee_et_sans_champs_sensibles(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    UtilisateurFabrique.create_batch(3)

    reponse = client.get(ROUTE_UTILISATEURS)

    assert reponse.status_code == 200
    assert set(reponse.data) == {"count", "next", "previous", "results"}
    assert reponse.data["count"] == 4
    assert reponse.data["next"] is None
    assert reponse.data["previous"] is None
    assert len(reponse.data["results"]) == 4
    for resultat in reponse.data["results"]:
        assert set(resultat) == CHAMPS_UTILISATEUR_ADMIN
        assert not {"id", "password", "is_superuser"} & set(resultat)
    assert reponse["Cache-Control"] == "no-store"
    assert reponse["Pragma"] == "no-cache"
    evenement = JournalSecurite.objects.get(
        type_evenement=TypeEvenementSecurite.LISTE_UTILISATEURS_CONSULTEE,
    )
    assert evenement.acteur == utilisateur_vendeur
    assert evenement.succes is True
    assert evenement.details == {"nombre_resultats": "4"}


@pytest.mark.django_db
def test_liste_vide_retourne_les_clefs_paginees_attendues(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.get(ROUTE_UTILISATEURS, {"role": "vendeur"})

    assert reponse.status_code == 200
    assert reponse.data == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }


@pytest.mark.django_db
def test_pagination_applique_page_et_taille(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    UtilisateurFabrique.create_batch(24)

    reponse = client.get(ROUTE_UTILISATEURS, {"page": 2, "page_size": 5})

    assert reponse.status_code == 200
    assert reponse.data["count"] == 25
    assert len(reponse.data["results"]) == 5
    assert reponse.data["next"] is not None
    assert reponse.data["previous"] is not None


@pytest.mark.django_db
def test_page_size_superieur_au_maximum_est_plafonne(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    UtilisateurFabrique.create_batch(101)

    reponse = client.get(ROUTE_UTILISATEURS, {"page_size": 1000})

    assert reponse.status_code == 200
    assert reponse.data["count"] == 102
    assert len(reponse.data["results"]) == 100
    assert reponse.data["next"] is not None


@pytest.mark.django_db
def test_recherche_couvre_nom_prenom_et_email_sans_casse(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    utilisateur_nom = UtilisateurFabrique(
        email="nom-special@exemple.test",
        nom="RechercheUnique",
        prenom="Autre",
    )
    utilisateur_prenom = UtilisateurFabrique(
        email="prenom-special@exemple.test",
        nom="Autre",
        prenom="RechercheUnique",
    )
    utilisateur_email = UtilisateurFabrique(
        email="ReCherCheUnique@exemple.test",
        nom="Email",
        prenom="Autre",
    )

    reponse = client.get(ROUTE_UTILISATEURS, {"search": "rechercheunique"})

    assert reponse.status_code == 200
    assert {resultat["uuid"] for resultat in reponse.data["results"]} == {
        str(utilisateur_nom.uuid),
        str(utilisateur_prenom.uuid),
        str(utilisateur_email.uuid),
    }


@pytest.mark.django_db
def test_filtres_role_et_active_sont_combinables(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    admin_actif = UtilisateurFabrique(email="admin-actif@exemple.test", role="admin")
    admin_inactif = UtilisateurFabrique(email="admin-inactif@exemple.test", role="admin")
    admin_inactif.is_active = False
    admin_inactif.save(update_fields=["is_active"])
    vendeur_inactif = UtilisateurFabrique(email="vendeur-inactif@exemple.test")
    vendeur_inactif.is_active = False
    vendeur_inactif.save(update_fields=["is_active"])

    reponse = client.get(ROUTE_UTILISATEURS, {"role": "admin", "active": "true"})

    assert reponse.status_code == 200
    assert {resultat["uuid"] for resultat in reponse.data["results"]} == {
        str(utilisateur_vendeur.uuid),
        str(admin_actif.uuid),
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("parametres", "champ"),
    [
        ({"role": "superadmin"}, "role"),
        ({"active": "oui"}, "active"),
        ({"ordering": "password"}, "ordering"),
        ({"ordering": "email,password"}, "ordering"),
    ],
)
def test_filtre_ou_tri_invalide_est_refuse(utilisateur_vendeur, parametres, champ):
    client = client_administrateur(utilisateur_vendeur)

    reponse = client.get(ROUTE_UTILISATEURS, parametres)

    assert reponse.status_code == 400
    assert reponse.data["code"] == "donnees_invalides"
    assert champ in reponse.data["erreurs"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("ordering", "attendu"),
    [
        ("nom", ["Alpha", "Moyen", "Zulu"]),
        ("-nom", ["Zulu", "Moyen", "Alpha"]),
        ("prenom", ["A", "B", "C"]),
        (
            "email",
            ["tri-a@exemple.test", "tri-b@exemple.test", "tri-c@exemple.test"],
        ),
        ("role", ["admin", "vendeur", "vendeur"]),
    ],
)
def test_tri_utilise_la_liste_blanche(ordering, attendu, utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    UtilisateurFabrique(email="tri-c@exemple.test", nom="Moyen", prenom="B", role="vendeur")
    UtilisateurFabrique(email="tri-a@exemple.test", nom="Alpha", prenom="A", role="admin")
    UtilisateurFabrique(email="tri-b@exemple.test", nom="Zulu", prenom="C", role="vendeur")

    reponse = client.get(
        ROUTE_UTILISATEURS,
        {"ordering": ordering, "page_size": 100, "search": "tri-"},
    )

    assert reponse.status_code == 200
    champ = ordering.lstrip("-")
    assert [resultat[champ] for resultat in reponse.data["results"]] == attendu


@pytest.mark.django_db
def test_ordre_par_defaut_est_nom_et_stable(utilisateur_vendeur):
    client = client_administrateur(utilisateur_vendeur)
    premier = UtilisateurFabrique(email="tri-premier@exemple.test", nom="Même", prenom="A")
    second = UtilisateurFabrique(email="tri-second@exemple.test", nom="Même", prenom="B")

    reponse = client.get(ROUTE_UTILISATEURS, {"page_size": 100, "search": "tri-"})

    assert reponse.status_code == 200
    assert [resultat["uuid"] for resultat in reponse.data["results"]] == [
        str(premier.uuid),
        str(second.uuid),
    ]


@pytest.mark.django_db
def test_nombre_de_requetes_sql_reste_constant_quel_que_soit_le_nombre_de_resultats(
    django_assert_num_queries,
    utilisateur_vendeur,
):
    client = client_administrateur(utilisateur_vendeur)
    petit_resultat = client.get(ROUTE_UTILISATEURS, {"page_size": 1})
    assert petit_resultat.status_code == 200
    UtilisateurFabrique.create_batch(10)

    with django_assert_num_queries(6):
        grand_resultat = client.get(ROUTE_UTILISATEURS, {"page_size": 100})

    assert grand_resultat.status_code == 200
    assert grand_resultat.data["count"] == petit_resultat.data["count"] + 10


@pytest.mark.django_db
def test_vendeur_est_interdit_de_lister(utilisateur_vendeur):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}")

    reponse = client.get(ROUTE_UTILISATEURS)

    assert reponse.status_code == 403
    assert reponse.data["code"] == "acces_interdit"


@pytest.mark.django_db
def test_administrateur_oblige_de_changer_son_mot_de_passe_est_bloque(utilisateur_vendeur):
    utilisateur_vendeur.role = "admin"
    utilisateur_vendeur.doit_changer_mot_de_passe = True
    utilisateur_vendeur.save(update_fields=["role", "doit_changer_mot_de_passe"])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(utilisateur_vendeur)}")

    reponse = client.get(ROUTE_UTILISATEURS)

    assert reponse.status_code == 403
    assert reponse.data["code"] == "changement_mot_de_passe_requis"


@pytest.mark.django_db
def test_anonyme_est_refuse_de_lister():
    reponse = APIClient().get(ROUTE_UTILISATEURS)

    assert reponse.status_code == 401
    assert reponse.data["code"] == "non_authentifie"
