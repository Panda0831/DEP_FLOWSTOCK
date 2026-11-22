"""Vérifie les réponses réelles contre le catalogue JSON partagé avec Swagger."""

import re
from collections.abc import Mapping
from datetime import datetime
from uuid import UUID

import pytest
from django.conf import settings
from django.core.cache import cache
from django.core.validators import validate_email
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.exemples_json import EXEMPLES_JSON_CONNEXION
from apps.accounts.tests.test_connexion import MOT_DE_PASSE_VALIDE, ROUTE_CONNEXION

_STATUTS_HTTP = {
    "succes": 200,
    "validation": 400,
    "champs_inconnus": 400,
    "json_malforme": 400,
    "identifiants_invalides": 401,
    "methode_non_autorisee": 405,
    "type_contenu_non_pris_en_charge": 415,
    "trop_de_requetes": 429,
    "erreur_interne": 500,
}


@pytest.fixture(autouse=True)
def vider_cache_connexion():
    cache.clear()


def verifier_forme_json(reponse_reelle, exemple_documente):
    """Compare exactement la structure et les valeurs stables de deux objets JSON."""
    _verifier_valeur(reponse_reelle.data, exemple_documente)


def _verifier_valeur(valeur_reelle, valeur_documentee, cle: str = "") -> None:
    if isinstance(valeur_documentee, Mapping):
        assert isinstance(valeur_reelle, Mapping)
        assert set(valeur_reelle) == set(valeur_documentee)
        for cle_enfant, valeur in valeur_documentee.items():
            _verifier_valeur(valeur_reelle[cle_enfant], valeur, cle_enfant)
        return

    if isinstance(valeur_documentee, list):
        assert isinstance(valeur_reelle, list)
        assert len(valeur_reelle) == len(valeur_documentee)
        for element_reel, element_documente in zip(
            valeur_reelle,
            valeur_documentee,
            strict=True,
        ):
            _verifier_valeur(element_reel, element_documente)
        return

    if isinstance(valeur_documentee, bool):
        assert type(valeur_reelle) is bool
        assert valeur_reelle is valeur_documentee
        return

    if cle in {"access", "refresh"}:
        assert isinstance(valeur_reelle, str)
        assert re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", valeur_reelle)
        return

    if cle == "uuid":
        assert isinstance(valeur_reelle, str)
        assert str(UUID(valeur_reelle)) == valeur_reelle
        return

    if cle == "email":
        assert isinstance(valeur_reelle, str)
        validate_email(valeur_reelle)
        return

    if cle in {
        "date_creation",
        "derniere_connexion",
        "date_dernier_changement_mot_de_passe",
        "date_modification",
    }:
        if valeur_documentee is None:
            assert valeur_reelle is None
            return
        assert isinstance(valeur_reelle, str)
        assert datetime.fromisoformat(valeur_reelle).utcoffset() is not None
        return

    assert isinstance(valeur_reelle, type(valeur_documentee))
    assert valeur_reelle == valeur_documentee


@pytest.mark.django_db
@pytest.mark.parametrize("cas", tuple(_STATUTS_HTTP))
def test_reponse_reelle_conforme_a_chaque_exemple_documente(
    cas,
    utilisateur_vendeur,
    monkeypatch,
):
    client = APIClient()

    if cas == "succes":
        reponse = client.post(
            ROUTE_CONNEXION,
            {"email": utilisateur_vendeur.email, "mot_de_passe": MOT_DE_PASSE_VALIDE},
            format="json",
        )
    elif cas == "validation":
        reponse = client.post(
            ROUTE_CONNEXION,
            {"email": "adresse-invalide", "mot_de_passe": MOT_DE_PASSE_VALIDE},
            format="json",
        )
    elif cas == "champs_inconnus":
        reponse = client.post(
            ROUTE_CONNEXION,
            {
                "email": utilisateur_vendeur.email,
                "mot_de_passe": MOT_DE_PASSE_VALIDE,
                "role": "admin",
            },
            format="json",
        )
    elif cas == "json_malforme":
        reponse = client.generic(
            "POST",
            ROUTE_CONNEXION,
            data=b'{"email":',
            content_type="application/json",
        )
    elif cas == "identifiants_invalides":
        reponse = client.post(
            ROUTE_CONNEXION,
            {"email": utilisateur_vendeur.email, "mot_de_passe": "incorrect"},
            format="json",
        )
    elif cas == "methode_non_autorisee":
        reponse = client.get(ROUTE_CONNEXION)
    elif cas == "type_contenu_non_pris_en_charge":
        reponse = client.generic(
            "POST",
            ROUTE_CONNEXION,
            data="email=rakoto%40exemple.com",
            content_type="text/plain",
        )
    elif cas == "trop_de_requetes":
        limites = {
            **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
            "connexion": "0/min",
            "connexion_par_email": "100/hour",
        }
        with override_settings(
            REST_FRAMEWORK={
                **settings.REST_FRAMEWORK,
                "DEFAULT_THROTTLE_RATES": limites,
            }
        ):
            reponse = client.post(
                ROUTE_CONNEXION,
                {"email": utilisateur_vendeur.email, "mot_de_passe": MOT_DE_PASSE_VALIDE},
                format="json",
            )
    else:

        def provoquer_erreur(*args, **kwargs):
            raise RuntimeError("détail technique non exposable")

        monkeypatch.setattr(
            "apps.accounts.views.connexion.authentifier_utilisateur",
            provoquer_erreur,
        )
        reponse = client.post(
            ROUTE_CONNEXION,
            {"email": utilisateur_vendeur.email, "mot_de_passe": MOT_DE_PASSE_VALIDE},
            format="json",
        )

    assert reponse.status_code == _STATUTS_HTTP[cas]
    verifier_forme_json(reponse, EXEMPLES_JSON_CONNEXION[cas])
