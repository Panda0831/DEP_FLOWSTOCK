"""Routes du module utilisateurs."""

from django.urls import path

from apps.accounts.views.connexion import ConnexionVue
from apps.accounts.views.creation import CreationUtilisateurVue
from apps.accounts.views.deconnexion import DeconnexionVue
from apps.accounts.views.desactivation import DesactivationUtilisateurVue
from apps.accounts.views.detail import (
    DetailUtilisateurVue,
    UUIDUtilisateurInvalideVue,
)
from apps.accounts.views.jetons import RafraichissementJetonsVue
from apps.accounts.views.mots_de_passe import (
    ChangementMotDePasseVue,
    ConfirmationReinitialisationMotDePasseVue,
    DemandeReinitialisationMotDePasseVue,
)
from apps.accounts.views.profil import MonProfilVue

app_name = "accounts"
urlpatterns = [
    path("auth/login/", ConnexionVue.as_view(), name="connexion"),
    path(
        "auth/token/refresh/",
        RafraichissementJetonsVue.as_view(),
        name="rafraichissement_jetons",
    ),
    path("auth/me/", MonProfilVue.as_view(), name="mon_profil"),
    path(
        "auth/password/change/",
        ChangementMotDePasseVue.as_view(),
        name="changer_mot_de_passe",
    ),
    path(
        "auth/password/reset/request/",
        DemandeReinitialisationMotDePasseVue.as_view(),
        name="demander_reinitialisation_mot_de_passe",
    ),
    path(
        "auth/password/reset/confirm/",
        ConfirmationReinitialisationMotDePasseVue.as_view(),
        name="confirmer_reinitialisation_mot_de_passe",
    ),
    path("auth/logout/", DeconnexionVue.as_view(), name="deconnexion"),
    path("users/", CreationUtilisateurVue.as_view(), name="creer_utilisateur"),
    path(
        "users/<uuid:uuid>/",
        DetailUtilisateurVue.as_view(),
        name="detail_utilisateur",
    ),
    path(
        "users/<uuid:uuid>/deactivate/",
        DesactivationUtilisateurVue.as_view(),
        name="desactiver_utilisateur",
    ),
    path(
        "users/<str:uuid>/",
        UUIDUtilisateurInvalideVue.as_view(),
        name="uuid_utilisateur_invalide",
    ),
    path(
        "users/<str:uuid>/deactivate/",
        UUIDUtilisateurInvalideVue.as_view(),
        name="uuid_desactivation_invalide",
    ),
]
