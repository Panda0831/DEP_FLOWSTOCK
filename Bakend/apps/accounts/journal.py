"""Enregistrement des événements de sécurité liés aux comptes."""

import logging
from collections.abc import Mapping

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import DatabaseError, transaction
from django.http import HttpRequest

from apps.accounts.constantes import (
    LONGUEUR_MAXIMALE_AGENT_UTILISATEUR,
    LONGUEUR_MAXIMALE_EMAIL,
    LONGUEUR_MAXIMALE_METHODE,
    LONGUEUR_MAXIMALE_ROUTE,
)
from apps.accounts.models import JournalSecurite, TypeEvenementSecurite, Utilisateur
from apps.core.reseau import adresse_ip_client

_journal = logging.getLogger("stockflow.securite")
type DetailsSecurite = Mapping[str, str | list[str]]


def journaliser_evenement(
    requete: HttpRequest,
    type_evenement: TypeEvenementSecurite,
    *,
    email_saisi: str = "",
    utilisateur: Utilisateur | None = None,
    utilisateur_cible: Utilisateur | None = None,
    details: DetailsSecurite | None = None,
    obligatoire: bool = False,
) -> None:
    """Enregistre des métadonnées non secrètes sans faire échouer les tentatives invalides."""
    email = _email_valide(email_saisi)
    evenement = JournalSecurite(
        type_evenement=type_evenement,
        succes=type_evenement
        not in {
            TypeEvenementSecurite.CONNEXION_ECHOUEE,
            TypeEvenementSecurite.JETON_REJETE,
            TypeEvenementSecurite.ACCES_REFUSE,
        },
        acteur=utilisateur,
        utilisateur_cible=utilisateur_cible if utilisateur_cible is not None else utilisateur,
        email_saisi=email,
        adresse_ip=adresse_ip_client(requete),
        agent_utilisateur=requete.META.get("HTTP_USER_AGENT", "")[
            :LONGUEUR_MAXIMALE_AGENT_UTILISATEUR
        ],
        route=requete.path[:LONGUEUR_MAXIMALE_ROUTE],
        methode=requete.method[:LONGUEUR_MAXIMALE_METHODE],
        details=details or {},
    )

    try:
        with transaction.atomic():
            evenement.save(force_insert=True)
    except DatabaseError as erreur:
        _journal.error(
            "Échec de persistance du journal de sécurité: type=%s",
            type(erreur).__name__,
        )
        if obligatoire:
            raise


def _email_valide(valeur: str) -> str:
    if not isinstance(valeur, str) or not valeur or len(valeur) > LONGUEUR_MAXIMALE_EMAIL:
        return ""
    adresse = valeur.strip().lower()
    try:
        validate_email(adresse)
    except ValidationError:
        return ""
    return adresse
