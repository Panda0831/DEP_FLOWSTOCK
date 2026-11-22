"""Services métier de l’authentification des comptes."""

import logging
from smtplib import SMTPException
from threading import Thread
from typing import TypedDict
from urllib.parse import urlencode
from uuid import UUID

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import HttpRequest
from django.utils import timezone
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework_simplejwt.exceptions import ExpiredTokenError, TokenError
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken

from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import TypeEvenementSecurite, Utilisateur

_HASH_MOT_DE_PASSE_FICTIF = make_password("MotDePasseFictif!StockFlow2026")
_GENERATEUR_JETON_REINITIALISATION = PasswordResetTokenGenerator()
_journal = logging.getLogger("stockflow.securite")


class JetonsConnexion(TypedDict):
    """Paire de jetons sérialisables renvoyée après connexion."""

    access: str
    refresh: str


def authentifier_utilisateur(
    email: str,
    mot_de_passe: str,
    requete,
) -> tuple[Utilisateur, JetonsConnexion]:
    """Vérifie les identifiants et journalise tout succès ou échec métier."""
    raison_echec: str | None = None
    utilisateur_authentifie: Utilisateur | None = None
    jetons: JetonsConnexion | None = None

    with transaction.atomic():
        utilisateur = Utilisateur.objects.select_for_update().filter(email=email).first()

        if utilisateur is None:
            verifier_mot_de_passe_factice(mot_de_passe)
            raison_echec = "email_inconnu"
        elif not utilisateur.check_password(mot_de_passe):
            raison_echec = "mot_de_passe_incorrect"
        elif not utilisateur.is_active:
            raison_echec = "compte_inactif"
        else:
            utilisateur.last_login = timezone.now()
            utilisateur.save(update_fields=["last_login"])
            jetons = creer_jetons_connexion(utilisateur)
            utilisateur_authentifie = utilisateur
            journaliser_evenement(
                requete,
                TypeEvenementSecurite.CONNEXION_REUSSIE,
                email_saisi=email,
                utilisateur=utilisateur,
                obligatoire=True,
            )

        if raison_echec is not None:
            journaliser_evenement(
                requete,
                TypeEvenementSecurite.CONNEXION_ECHOUEE,
                email_saisi=email,
                utilisateur=utilisateur,
                details={"raison": raison_echec},
                obligatoire=True,
            )

    if raison_echec is not None:
        raise AuthenticationFailed(
            "E-mail ou mot de passe incorrect.",
            code="identifiants_invalides",
        )

    if utilisateur_authentifie is None or jetons is None:
        raise RuntimeError("État incohérent après authentification.")

    return utilisateur_authentifie, jetons


def verifier_mot_de_passe_factice(mot_de_passe: str) -> None:
    """Effectue un hachage de vérification lorsque l’adresse n’existe pas."""
    check_password(mot_de_passe, _HASH_MOT_DE_PASSE_FICTIF)


def creer_jetons_connexion(utilisateur: Utilisateur) -> JetonsConnexion:
    """Crée un JWT d’accès et son JWT de rafraîchissement."""
    jeton_rafraichissement = RefreshToken.for_user(utilisateur)
    return {
        "access": str(jeton_rafraichissement.access_token),
        "refresh": str(jeton_rafraichissement),
    }


class EchecRafraichissement(AuthenticationFailed):
    """Échec d’authentification public avec cause interne réservée au journal."""

    def __init__(
        self,
        raison_interne: str,
        code_public: str = "jeton_invalide",
    ) -> None:
        self.raison_interne = raison_interne
        super().__init__("Le jeton de rafraîchissement est invalide.", code=code_public)


class EchecDeconnexion(APIException):
    """Erreur client pour un jeton de rafraîchissement invalide."""

    status_code = 400
    default_detail = "Le jeton de rafraîchissement est invalide."
    default_code = "jeton_invalide"


class ConflitEmail(APIException):
    """Conflit de concurrence lors de la création d’une adresse déjà utilisée."""

    status_code = 409
    default_detail = "Cette adresse e-mail est déjà utilisée."
    default_code = "email_deja_utilise"


def rafraichir_jetons(jeton_brut: str) -> JetonsConnexion:
    """Valide, verrouille puis révoque le jeton source avant d’en délivrer un nouveau."""
    try:
        with transaction.atomic():
            jeton = RefreshToken(jeton_brut)
            identifiant_utilisateur = jeton.get(jwt_settings.USER_ID_CLAIM)
            if identifiant_utilisateur is None:
                raise EchecRafraichissement("identifiant_utilisateur_absent")

            utilisateur = (
                Utilisateur.objects.select_for_update()
                .filter(**{jwt_settings.USER_ID_FIELD: identifiant_utilisateur})
                .first()
            )
            if utilisateur is None:
                raise EchecRafraichissement("compte_introuvable")
            if not utilisateur.is_active:
                raise EchecRafraichissement("compte_inactif")

            jti = jeton[jwt_settings.JTI_CLAIM]
            jeton.outstand()
            OutstandingToken.objects.select_for_update().get(jti=jti)
            jeton.check_blacklist()

            nouveaux_jetons = creer_jetons_connexion(utilisateur)
            jeton.blacklist()
            return nouveaux_jetons
    except ExpiredTokenError as erreur:
        raise EchecRafraichissement("jeton_expire", "jeton_expire") from erreur
    except TokenError as erreur:
        raise EchecRafraichissement("jeton_invalide") from erreur


def creer_utilisateur_par_administrateur(
    donnees: dict[str, str],
    administrateur: Utilisateur,
    requete,
) -> Utilisateur:
    """Crée un compte temporaire et journalise l’opération dans la même transaction."""
    email = donnees["email"]
    try:
        with transaction.atomic():
            if Utilisateur.objects.filter(email__iexact=email).exists():
                raise ValidationError(
                    {"email": ["Cette adresse e-mail est déjà utilisée."]},
                )

            try:
                utilisateur = Utilisateur.objects.creer_utilisateur(
                    email=email,
                    nom=donnees["nom"],
                    prenom=donnees["prenom"],
                    telephone=donnees.get("telephone", ""),
                    role=donnees.get("role", "vendeur"),
                    mot_de_passe=donnees["mot_de_passe_initial"],
                    doit_changer_mot_de_passe=True,
                )
            except DjangoValidationError as erreur:
                raise ValidationError(
                    {"mot_de_passe_initial": erreur.messages},
                ) from erreur

            journaliser_evenement(
                requete,
                TypeEvenementSecurite.UTILISATEUR_CREE,
                utilisateur=administrateur,
                utilisateur_cible=utilisateur,
                details={"role": utilisateur.role},
                obligatoire=True,
            )
            return utilisateur
    except IntegrityError as erreur:
        cause = getattr(erreur, "__cause__", None)
        nom_contrainte = getattr(getattr(cause, "diag", None), "constraint_name", None)
        if nom_contrainte in {
            "uniq_utilisateurs_email_minuscule",
            "utilisateurs_email_key",
        }:
            raise ConflitEmail from erreur
        raise


class AutoModificationRoleInterdite(PermissionDenied):
    """Un administrateur ne peut pas modifier son propre rôle."""

    default_detail = "Un administrateur ne peut pas modifier son propre rôle."
    default_code = "auto_modification_role_interdite"


class DernierAdministrateur(APIException):
    """Empêche la rétrogradation du dernier administrateur actif."""

    status_code = 409
    default_detail = "Le dernier administrateur actif ne peut pas être rétrogradé."
    default_code = "dernier_administrateur"


class AutoDesactivationInterdite(PermissionDenied):
    """Un administrateur ne peut pas désactiver son propre compte."""

    default_detail = "Un administrateur ne peut pas se désactiver lui-même."
    default_code = "auto_desactivation_interdite"


class CompteDejaDesactive(APIException):
    """Signale une demande de désactivation déjà appliquée."""

    status_code = 409
    default_detail = "Ce compte est déjà désactivé."
    default_code = "compte_deja_desactive"


class DernierAdministrateurActif(APIException):
    """Empêche la désactivation du dernier administrateur actif."""

    status_code = 409
    default_detail = "Le dernier administrateur actif ne peut pas être désactivé."
    default_code = "dernier_administrateur"


def modifier_utilisateur_par_administrateur(
    uuid_utilisateur: UUID,
    donnees: dict[str, str],
    administrateur: Utilisateur,
    requete: HttpRequest,
) -> Utilisateur:
    """Modifie un compte avec verrouillage, révocation JWT et journal atomiques."""
    try:
        with transaction.atomic():
            administrateurs_actifs = []
            if "role" in donnees:
                administrateurs_actifs = list(
                    Utilisateur.objects.select_for_update()
                    .filter(role="admin", is_active=True)
                    .order_by("id")
                )

            utilisateur = (
                Utilisateur.objects.select_for_update().filter(uuid=uuid_utilisateur).first()
            )
            if utilisateur is None:
                raise NotFound()
            if "role" in donnees and utilisateur.pk == administrateur.pk:
                raise AutoModificationRoleInterdite()

            ancien_role = utilisateur.role
            ancien_email = utilisateur.email
            if (
                donnees.get("role") == "vendeur"
                and ancien_role == "admin"
                and utilisateur.is_active
                and len(administrateurs_actifs) <= 1
            ):
                raise DernierAdministrateur()
            if "role" in donnees and not any(
                compte.pk == administrateur.pk for compte in administrateurs_actifs
            ):
                raise PermissionDenied(
                    "Cette action est réservée aux administrateurs.",
                    code="acces_interdit",
                )

            email = donnees.get("email")
            if email is not None and email != ancien_email:
                email_deja_utilise = (
                    Utilisateur.objects.filter(email__iexact=email)
                    .exclude(pk=utilisateur.pk)
                    .exists()
                )
                if email_deja_utilise:
                    raise ValidationError(
                        {"email": ["Cette adresse e-mail est déjà utilisée."]},
                    )

            champs_modifies = [
                champ for champ, valeur in donnees.items() if getattr(utilisateur, champ) != valeur
            ]
            if not champs_modifies:
                return utilisateur

            for champ in champs_modifies:
                setattr(utilisateur, champ, donnees[champ])
            utilisateur.save(update_fields=[*champs_modifies, "date_modification"])

            if {"role", "email"} & set(champs_modifies):
                _revoquer_jetons_rafraichissement(utilisateur)

            journaliser_evenement(
                requete,
                TypeEvenementSecurite.UTILISATEUR_MODIFIE,
                utilisateur=administrateur,
                utilisateur_cible=utilisateur,
                details={"champs_modifies": sorted(champs_modifies)},
                obligatoire=True,
            )
            if "role" in champs_modifies:
                journaliser_evenement(
                    requete,
                    TypeEvenementSecurite.ROLE_MODIFIE,
                    utilisateur=administrateur,
                    utilisateur_cible=utilisateur,
                    details={
                        "ancien_role": ancien_role,
                        "nouveau_role": utilisateur.role,
                    },
                    obligatoire=True,
                )
            return utilisateur
    except IntegrityError as erreur:
        cause = getattr(erreur, "__cause__", None)
        nom_contrainte = getattr(getattr(cause, "diag", None), "constraint_name", None)
        if nom_contrainte in {
            "uniq_utilisateurs_email_minuscule",
            "utilisateurs_email_key",
        }:
            raise ConflitEmail from erreur
        raise


def _revoquer_jetons_rafraichissement(utilisateur: Utilisateur) -> None:
    """Place en liste noire tous les refresh connus du compte sans modifier l’historique."""
    jetons = OutstandingToken.objects.select_for_update().filter(user=utilisateur).order_by("id")
    for jeton in jetons:
        BlacklistedToken.objects.get_or_create(token=jeton)


class AncienMotDePasseIncorrect(APIException):
    """Signale que le mot de passe actuel ne correspond pas au compte."""

    status_code = 400
    default_detail = "L’ancien mot de passe est incorrect."
    default_code = "ancien_mot_de_passe_incorrect"


class LienReinitialisationInvalide(APIException):
    """Uniformise les échecs de validation du lien de réinitialisation."""

    status_code = 400
    default_detail = "Lien de réinitialisation invalide ou expiré."
    default_code = "jeton_invalide"


def changer_mot_de_passe_utilisateur(
    identifiant_utilisateur: int,
    ancien_mot_de_passe: str,
    nouveau_mot_de_passe: str,
    requete: HttpRequest,
) -> None:
    """Change le mot de passe après vérification atomique de l’ancien."""
    with transaction.atomic():
        utilisateur = (
            Utilisateur.objects.select_for_update().filter(pk=identifiant_utilisateur).first()
        )
        if utilisateur is None:
            raise NotFound()
        if not utilisateur.check_password(ancien_mot_de_passe):
            raise AncienMotDePasseIncorrect()
        _enregistrer_nouveau_mot_de_passe(
            utilisateur,
            nouveau_mot_de_passe,
            requete,
            TypeEvenementSecurite.MOT_DE_PASSE_CHANGE,
        )


def demander_reinitialisation_mot_de_passe(email: str, requete: HttpRequest) -> None:
    """Journalise la demande et prépare un e-mail sans révéler l’existence du compte."""
    utilisateur = Utilisateur.objects.filter(email__iexact=email).first()
    actif = utilisateur is not None and utilisateur.is_active
    jeton = _GENERATEUR_JETON_REINITIALISATION.make_token(utilisateur) if actif else None
    details = {"compte_existant": "true" if utilisateur is not None else "false"}
    journaliser_evenement(
        requete,
        TypeEvenementSecurite.REINITIALISATION_DEMANDEE,
        email_saisi=email,
        utilisateur=utilisateur,
        utilisateur_cible=utilisateur,
        details=details,
        obligatoire=True,
    )
    if actif and jeton is not None:
        try:
            Thread(
                target=_envoyer_email_reinitialisation,
                args=(email, str(utilisateur.uuid), jeton),
                daemon=True,
            ).start()
        except RuntimeError as erreur:
            _journal.error(
                "Échec de démarrage de l’envoi de réinitialisation: type=%s",
                type(erreur).__name__,
            )


def _envoyer_email_reinitialisation(email: str, uuid_utilisateur: str, jeton: str) -> None:
    """Envoie le lien de réinitialisation dans un thread sans journaliser le jeton."""
    base_url = settings.URL_FRONTEND_REINITIALISATION
    if not base_url:
        _journal.error("URL_FRONTEND_REINITIALISATION n’est pas configurée.")
        return

    separateur = "&" if "?" in base_url else "?"
    lien = f"{base_url}{separateur}{urlencode({'uid': uuid_utilisateur, 'token': jeton})}"
    message = (
        "Bonjour,\n\n"
        "Une demande de réinitialisation du mot de passe de votre compte StockFlow "
        "a été reçue. Ouvrez le lien suivant pour choisir un nouveau mot de passe :\n\n"
        f"{lien}\n\n"
        "Ce lien est valable une heure et ne peut être utilisé qu’une seule fois.\n"
        "Si vous n’êtes pas à l’origine de cette demande, ignorez ce message."
    )
    try:
        send_mail(
            "Réinitialisation de votre mot de passe StockFlow",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except (OSError, SMTPException) as erreur:
        _journal.error(
            "Échec d’envoi du courriel de réinitialisation: type=%s",
            type(erreur).__name__,
        )


def confirmer_reinitialisation_mot_de_passe(
    uuid_utilisateur: UUID,
    jeton: str,
    nouveau_mot_de_passe: str,
    confirmation_nouveau_mot_de_passe: str,
    requete: HttpRequest,
) -> None:
    """Valide le lien à usage unique et réinitialise le mot de passe atomiquement."""
    with transaction.atomic():
        utilisateur = Utilisateur.objects.select_for_update().filter(uuid=uuid_utilisateur).first()
        if (
            utilisateur is None
            or not utilisateur.is_active
            or not _GENERATEUR_JETON_REINITIALISATION.check_token(utilisateur, jeton)
        ):
            raise LienReinitialisationInvalide()
        if nouveau_mot_de_passe != confirmation_nouveau_mot_de_passe:
            raise ValidationError(
                {
                    "confirmation_nouveau_mot_de_passe": [
                        "La confirmation du mot de passe ne correspond pas."
                    ]
                }
            )
        try:
            validate_password(nouveau_mot_de_passe, utilisateur)
        except DjangoValidationError as erreur:
            raise ValidationError(
                {"nouveau_mot_de_passe": erreur.messages},
            ) from erreur
        _enregistrer_nouveau_mot_de_passe(
            utilisateur,
            nouveau_mot_de_passe,
            requete,
            TypeEvenementSecurite.MOT_DE_PASSE_REINITIALISE,
        )


def _enregistrer_nouveau_mot_de_passe(
    utilisateur: Utilisateur,
    nouveau_mot_de_passe: str,
    requete: HttpRequest,
    type_evenement: TypeEvenementSecurite,
) -> None:
    """Persiste le secret haché, ferme les sessions et journalise l’opération."""
    utilisateur.set_password(nouveau_mot_de_passe)
    utilisateur.doit_changer_mot_de_passe = False
    utilisateur.date_dernier_changement_mot_de_passe = timezone.now()
    utilisateur.save(
        update_fields=[
            "password",
            "doit_changer_mot_de_passe",
            "date_dernier_changement_mot_de_passe",
            "date_modification",
        ]
    )
    _revoquer_jetons_rafraichissement(utilisateur)
    journaliser_evenement(
        requete,
        type_evenement,
        utilisateur=utilisateur,
        utilisateur_cible=utilisateur,
        obligatoire=True,
    )


def modifier_profil_utilisateur(
    utilisateur_identifiant: int,
    donnees: dict[str, str],
    requete: HttpRequest,
) -> Utilisateur:
    """Met à jour les champs du profil et journalise uniquement les valeurs modifiées."""
    with transaction.atomic():
        utilisateur = (
            Utilisateur.objects.select_for_update().filter(pk=utilisateur_identifiant).first()
        )
        if utilisateur is None:
            raise NotFound()
        champs_modifies = [
            champ for champ, valeur in donnees.items() if getattr(utilisateur, champ) != valeur
        ]
        if not champs_modifies:
            return utilisateur
        for champ in champs_modifies:
            setattr(utilisateur, champ, donnees[champ])
        utilisateur.save(update_fields=[*champs_modifies, "date_modification"])
        journaliser_evenement(
            requete,
            TypeEvenementSecurite.PROFIL_MODIFIE,
            utilisateur=utilisateur,
            utilisateur_cible=utilisateur,
            details={"champs_modifies": sorted(champs_modifies)},
            obligatoire=True,
        )
        return utilisateur


def desactiver_utilisateur_par_administrateur(
    uuid_utilisateur: UUID,
    administrateur: Utilisateur,
    requete: HttpRequest,
) -> Utilisateur:
    """Désactive un compte et révoque ses jetons dans une transaction atomique."""
    with transaction.atomic():
        administrateurs_actifs = list(
            Utilisateur.objects.select_for_update()
            .filter(role="admin", is_active=True)
            .order_by("id")
        )
        utilisateur = Utilisateur.objects.select_for_update().filter(uuid=uuid_utilisateur).first()
        if utilisateur is None:
            raise NotFound()
        if utilisateur.pk == administrateur.pk:
            raise AutoDesactivationInterdite()
        if not utilisateur.is_active:
            raise CompteDejaDesactive()
        if utilisateur.role == "admin" and len(administrateurs_actifs) <= 1:
            raise DernierAdministrateurActif()
        if not any(compte.pk == administrateur.pk for compte in administrateurs_actifs):
            raise PermissionDenied(
                "Cette action est réservée aux administrateurs.",
                code="acces_interdit",
            )

        utilisateur.is_active = False
        utilisateur.save(update_fields=["is_active", "date_modification"])
        _revoquer_jetons_rafraichissement(utilisateur)
        journaliser_evenement(
            requete,
            TypeEvenementSecurite.COMPTE_DESACTIVE,
            utilisateur=administrateur,
            utilisateur_cible=utilisateur,
            obligatoire=True,
        )
        return utilisateur


def deconnecter_utilisateur(jeton_brut: str, utilisateur: Utilisateur, requete) -> None:
    """Révoque idempotemment le refresh s’il appartient à l’utilisateur connecté."""
    try:
        jeton_valide = UntypedToken(jeton_brut)
        if jeton_valide.get("token_type") != "refresh":
            raise EchecDeconnexion

        identifiant_jeton = jeton_valide.get(jwt_settings.USER_ID_CLAIM)
        identifiant_utilisateur = getattr(utilisateur, jwt_settings.USER_ID_FIELD)
        if identifiant_jeton is None:
            raise EchecDeconnexion
        if str(identifiant_jeton) != str(identifiant_utilisateur):
            raise PermissionDenied(
                "Ce jeton n’appartient pas à l’utilisateur authentifié.",
                code="jeton_non_autorise",
            )

        jti = jeton_valide[jwt_settings.JTI_CLAIM]
        with transaction.atomic():
            jeton_existant = (
                OutstandingToken.objects.select_for_update().filter(jti=jti).order_by().first()
            )
            if not BlacklistedToken.objects.filter(token__jti=jti).exists():
                jeton_rafraichissement = RefreshToken(jeton_brut)
                if jeton_existant is None:
                    jeton_rafraichissement.outstand()
                    OutstandingToken.objects.select_for_update().get(jti=jti)
                jeton_rafraichissement.blacklist()

            journaliser_evenement(
                requete,
                TypeEvenementSecurite.DECONNEXION,
                utilisateur=utilisateur,
                obligatoire=True,
            )
    except (ExpiredTokenError, TokenError) as erreur:
        raise EchecDeconnexion from erreur
