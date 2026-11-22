"""Vérifie les branches défensives des services d’authentification."""

import logging
from smtplib import SMTPException
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.db import IntegrityError
from django.test import RequestFactory, override_settings
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts import services
from apps.accounts.models import JournalSecurite, TypeEvenementSecurite, Utilisateur

MOT_DE_PASSE = "Fleur!Miroir8472"


def requete_http():
    return RequestFactory().post("/api/v1/test/")


@pytest.mark.django_db
def test_authentification_signale_un_etat_interne_incoherent(utilisateur_vendeur, monkeypatch):
    monkeypatch.setattr(services, "creer_jetons_connexion", lambda utilisateur: None)

    with pytest.raises(RuntimeError, match="État incohérent"):
        services.authentifier_utilisateur(
            utilisateur_vendeur.email,
            MOT_DE_PASSE,
            requete_http(),
        )


@pytest.mark.django_db
def test_rafraichissement_refuse_un_jeton_sans_identifiant_utilisateur(utilisateur_vendeur):
    jeton = RefreshToken.for_user(utilisateur_vendeur)
    del jeton["utilisateur_uuid"]

    with pytest.raises(services.EchecRafraichissement):
        services.rafraichir_jetons(str(jeton))


@pytest.mark.django_db
def test_rafraichissement_refuse_un_compte_introuvable(utilisateur_vendeur):
    jeton = RefreshToken.for_user(utilisateur_vendeur)
    jeton["utilisateur_uuid"] = str(uuid4())

    with pytest.raises(services.EchecRafraichissement):
        services.rafraichir_jetons(str(jeton))


@pytest.mark.django_db
def test_creation_retransmet_une_integrite_error_inconnue(utilisateur_vendeur, monkeypatch):
    utilisateur_vendeur.role = "admin"
    utilisateur_vendeur.save(update_fields=["role"])

    def lever_integrite(*args, **kwargs):
        raise IntegrityError("contrainte inattendue")

    monkeypatch.setattr(Utilisateur.objects, "creer_utilisateur", lever_integrite)
    donnees = {
        "email": "nouveau@exemple.test",
        "nom": "Nouveau",
        "prenom": "Compte",
        "mot_de_passe_initial": "Givre!Atlas5981",
    }

    with pytest.raises(IntegrityError, match="contrainte inattendue"):
        services.creer_utilisateur_par_administrateur(
            donnees,
            utilisateur_vendeur,
            requete_http(),
        )


@pytest.mark.django_db
def test_modification_role_refuse_un_acteur_absent_des_admins_actifs(utilisateur_vendeur):
    cible = Utilisateur.objects.creer_utilisateur(
        email="cible@exemple.test",
        nom="Cible",
        prenom="Compte",
        mot_de_passe=MOT_DE_PASSE,
    )

    with pytest.raises(PermissionDenied):
        services.modifier_utilisateur_par_administrateur(
            cible.uuid,
            {"role": "admin"},
            utilisateur_vendeur,
            requete_http(),
        )


@pytest.mark.django_db
def test_changement_email_revoque_les_jetons_de_rafraichissement(
    utilisateur_vendeur,
):
    administrateur = Utilisateur.objects.creer_utilisateur(
        email="admin@exemple.test",
        nom="Admin",
        prenom="StockFlow",
        mot_de_passe=MOT_DE_PASSE,
        role="admin",
        is_superuser=True,
    )
    jeton = RefreshToken.for_user(utilisateur_vendeur)

    resultat = services.modifier_utilisateur_par_administrateur(
        utilisateur_vendeur.uuid,
        {"email": "nouvelle-adresse@exemple.test"},
        administrateur,
        requete_http(),
    )

    entree = OutstandingToken.objects.get(jti=jeton["jti"])
    assert resultat.email == "nouvelle-adresse@exemple.test"
    assert BlacklistedToken.objects.filter(token=entree).exists()


@pytest.mark.django_db
def test_modification_nom_ne_revoque_pas_les_jetons(utilisateur_vendeur):
    administrateur = Utilisateur.objects.creer_utilisateur(
        email="admin@exemple.test",
        nom="Admin",
        prenom="StockFlow",
        mot_de_passe=MOT_DE_PASSE,
        role="admin",
        is_superuser=True,
    )
    jeton = RefreshToken.for_user(utilisateur_vendeur)

    services.modifier_utilisateur_par_administrateur(
        utilisateur_vendeur.uuid,
        {"nom": "Nouveau nom"},
        administrateur,
        requete_http(),
    )

    assert not BlacklistedToken.objects.filter(token__jti=jeton["jti"]).exists()


@pytest.mark.django_db
def test_modification_convertit_une_integrite_error_email_en_conflit(
    utilisateur_vendeur,
    monkeypatch,
):
    administrateur = Utilisateur.objects.creer_utilisateur(
        email="admin@exemple.test",
        nom="Admin",
        prenom="StockFlow",
        mot_de_passe=MOT_DE_PASSE,
        role="admin",
        is_superuser=True,
    )
    cause = RuntimeError("contrainte unique")
    cause.diag = SimpleNamespace(constraint_name="uniq_utilisateurs_email_minuscule")
    erreur = IntegrityError("adresse en conflit")
    erreur.__cause__ = cause

    def lever_integrite(instance, *args, **kwargs):
        raise erreur

    monkeypatch.setattr(Utilisateur, "save", lever_integrite)
    with pytest.raises(services.ConflitEmail):
        services.modifier_utilisateur_par_administrateur(
            utilisateur_vendeur.uuid,
            {"nom": "Nouveau nom"},
            administrateur,
            requete_http(),
        )


@pytest.mark.django_db
def test_modification_retransmet_une_integrite_error_inconnue(
    utilisateur_vendeur,
    monkeypatch,
):
    administrateur = Utilisateur.objects.creer_utilisateur(
        email="admin@exemple.test",
        nom="Admin",
        prenom="StockFlow",
        mot_de_passe=MOT_DE_PASSE,
        role="admin",
        is_superuser=True,
    )

    def lever_integrite(instance, *args, **kwargs):
        raise IntegrityError("contrainte inattendue")

    monkeypatch.setattr(Utilisateur, "save", lever_integrite)
    with pytest.raises(IntegrityError, match="contrainte inattendue"):
        services.modifier_utilisateur_par_administrateur(
            utilisateur_vendeur.uuid,
            {"nom": "Nouveau nom"},
            administrateur,
            requete_http(),
        )


@pytest.mark.django_db
def test_changement_mot_de_passe_refuse_un_identifiant_introuvable(utilisateur_vendeur):
    with pytest.raises(NotFound):
        services.changer_mot_de_passe_utilisateur(
            utilisateur_vendeur.pk + 1000000,
            MOT_DE_PASSE,
            "Givre!Atlas5981",
            requete_http(),
        )


@pytest.mark.django_db
def test_demande_reinitialisation_journalise_lechec_de_demarrage_du_thread(
    utilisateur_vendeur,
    monkeypatch,
    caplog,
):
    class ThreadEnEchec:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            raise RuntimeError("thread non disponible")

    monkeypatch.setattr(services, "Thread", ThreadEnEchec)
    with caplog.at_level(logging.ERROR, logger="stockflow.securite"):
        services.demander_reinitialisation_mot_de_passe(
            utilisateur_vendeur.email,
            requete_http(),
        )

    assert "Échec de démarrage de l’envoi de réinitialisation" in caplog.text
    assert "thread non disponible" not in caplog.text


def test_envoi_reinitialisation_journalise_url_frontend_absente(caplog):
    with (
        override_settings(URL_FRONTEND_REINITIALISATION=""),
        caplog.at_level(logging.ERROR, logger="stockflow.securite"),
    ):
        services._envoyer_email_reinitialisation(
            "vendeur@exemple.test",
            str(uuid4()),
            "jeton-prive",
        )

    assert "URL_FRONTEND_REINITIALISATION n’est pas configurée." in caplog.text
    assert "jeton-prive" not in caplog.text


def test_envoi_reinitialisation_ne_journalise_pas_une_erreur_smtp(monkeypatch, caplog):
    def echouer(*args, **kwargs):
        raise SMTPException("serveur indisponible")

    monkeypatch.setattr(services, "send_mail", echouer)
    with (
        override_settings(
            URL_FRONTEND_REINITIALISATION="https://app.exemple.test/reinitialiser",
        ),
        caplog.at_level(logging.ERROR, logger="stockflow.securite"),
    ):
        services._envoyer_email_reinitialisation(
            "vendeur@exemple.test",
            str(uuid4()),
            "jeton-prive",
        )

    assert "Échec d’envoi du courriel de réinitialisation" in caplog.text
    assert "serveur indisponible" not in caplog.text
    assert "jeton-prive" not in caplog.text


@pytest.mark.django_db
def test_modification_profil_refuse_un_identifiant_introuvable(utilisateur_vendeur):
    with pytest.raises(NotFound):
        services.modifier_profil_utilisateur(
            utilisateur_vendeur.pk + 1000000,
            {"nom": "Nouveau nom"},
            requete_http(),
        )


@pytest.mark.django_db
def test_desactivation_refuse_un_acteur_non_administrateur(
    utilisateur_vendeur,
):
    cible = Utilisateur.objects.creer_utilisateur(
        email="cible@exemple.test",
        nom="Cible",
        prenom="Compte",
        mot_de_passe=MOT_DE_PASSE,
    )

    with pytest.raises(PermissionDenied):
        services.desactiver_utilisateur_par_administrateur(
            cible.uuid,
            utilisateur_vendeur,
            requete_http(),
        )


@pytest.mark.django_db
def test_deconnexion_refuse_un_jeton_sans_identifiant_utilisateur(utilisateur_vendeur):
    jeton = RefreshToken.for_user(utilisateur_vendeur)
    del jeton["utilisateur_uuid"]

    with pytest.raises(services.EchecDeconnexion):
        services.deconnecter_utilisateur(
            str(jeton),
            utilisateur_vendeur,
            requete_http(),
        )


@pytest.mark.django_db
def test_deconnexion_cree_une_entree_jeton_absente_du_stockage(utilisateur_vendeur):
    jeton = RefreshToken.for_user(utilisateur_vendeur)
    OutstandingToken.objects.filter(jti=jeton["jti"]).delete()

    services.deconnecter_utilisateur(str(jeton), utilisateur_vendeur, requete_http())

    entree = OutstandingToken.objects.get(jti=jeton["jti"])
    assert BlacklistedToken.objects.filter(token=entree).exists()


@pytest.mark.django_db
def test_modification_profil_sans_changement_ne_journalise_pas(utilisateur_vendeur):
    resultat = services.modifier_profil_utilisateur(
        utilisateur_vendeur.pk,
        {"nom": utilisateur_vendeur.nom},
        requete_http(),
    )

    assert resultat.pk == utilisateur_vendeur.pk
    assert not JournalSecurite.objects.filter(
        utilisateur_cible=resultat,
        type_evenement=TypeEvenementSecurite.PROFIL_MODIFIE,
    ).exists()
