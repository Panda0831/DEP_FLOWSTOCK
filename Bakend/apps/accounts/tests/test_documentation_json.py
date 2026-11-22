"""Vérifie la génération et la fraîcheur de la référence JSON."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


def test_commande_genere_et_verifie_la_reference_json():
    sortie = StringIO()

    call_command("generer_reference_json", stdout=sortie)
    assert "Référence JSON générée" in sortie.getvalue()

    sortie = StringIO()
    call_command("generer_reference_json", "--verifier", stdout=sortie)
    assert "Référence JSON à jour." in sortie.getvalue()


def test_commande_refuse_une_reference_absente(monkeypatch, tmp_path):
    from apps.accounts.management.commands import generer_reference_json

    monkeypatch.setattr(
        generer_reference_json,
        "_FICHIER_REFERENCE",
        tmp_path / "REFERENCE_JSON_UTILISATEURS.md",
    )

    with pytest.raises(CommandError, match="Référence JSON absente"):
        call_command("generer_reference_json", "--verifier")


def test_commande_refuse_une_reference_perimee(monkeypatch, tmp_path):
    from apps.accounts.management.commands import generer_reference_json

    fichier = tmp_path / "REFERENCE_JSON_UTILISATEURS.md"
    fichier.write_text("ancienne référence", encoding="utf-8")
    monkeypatch.setattr(generer_reference_json, "_FICHIER_REFERENCE", fichier)

    with pytest.raises(CommandError, match="n’est pas à jour"):
        call_command("generer_reference_json", "--verifier")
