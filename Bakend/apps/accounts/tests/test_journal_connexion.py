"""Teste la journalisation non secrète des tentatives de connexion."""

import logging

import pytest
from django.db import DatabaseError
from django.test import RequestFactory

from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import JournalSecurite, TypeEvenementSecurite


@pytest.mark.django_db
def test_email_invalide_est_omis_et_agent_utilisateur_est_borne():
    requete = RequestFactory().post(
        "/api/v1/auth/login/",
        HTTP_USER_AGENT="a" * 300,
    )

    journaliser_evenement(
        requete,
        TypeEvenementSecurite.CONNEXION_ECHOUEE,
        email_saisi="adresse-invalide",
    )

    evenement = JournalSecurite.objects.get()
    assert evenement.email_saisi == ""
    assert len(evenement.agent_utilisateur) == 255


@pytest.mark.django_db
def test_panne_du_journal_est_signalee_et_peut_etre_rendue_bloquante(
    monkeypatch,
    caplog,
):
    def echec_persistance(self, *args, **kwargs):
        raise DatabaseError("détail non destiné au journal")

    monkeypatch.setattr(JournalSecurite, "save", echec_persistance)
    requete = RequestFactory().post("/api/v1/auth/login/")

    with caplog.at_level(logging.ERROR, logger="stockflow.securite"):
        journaliser_evenement(
            requete,
            TypeEvenementSecurite.CONNEXION_ECHOUEE,
        )

    assert "type=DatabaseError" in caplog.text
    assert "détail non destiné au journal" not in caplog.text

    with pytest.raises(DatabaseError):
        journaliser_evenement(
            requete,
            TypeEvenementSecurite.CONNEXION_ECHOUEE,
            obligatoire=True,
        )
