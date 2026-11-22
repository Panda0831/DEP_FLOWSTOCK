"""Format uniforme des erreurs HTTP de l’API."""

import logging
from typing import Any

from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

_journal = logging.getLogger("stockflow.securite")


def gestionnaire_exceptions(
    exception: Exception,
    contexte: dict[str, Any],
) -> Response:
    """Convertit les erreurs DRF en réponses françaises sans détail technique."""
    reponse = exception_handler(exception, contexte)

    if reponse is None or reponse.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        _journal.error("Erreur interne de l’API: type=%s", type(exception).__name__)
        return Response(
            {"detail": "Erreur interne du serveur.", "code": "erreur_interne"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = _code_machine(exception, reponse.status_code)
    if isinstance(exception, exceptions.ValidationError):
        reponse.data = {
            "detail": "Les données envoyées sont invalides.",
            "code": code,
            "erreurs": reponse.data,
        }
    elif isinstance(exception, (exceptions.ParseError, exceptions.UnsupportedMediaType)):
        reponse.data = {
            "detail": _detail_francais(exception, reponse.data),
            "code": code,
            "erreurs": {},
        }
    else:
        detail = _detail_francais(exception, reponse.data)
        reponse.data = {"detail": detail, "code": code}

    return reponse


def _code_machine(exception: Exception, code_http: int) -> str:
    if isinstance(exception, exceptions.APIException):
        codes_exception = exception.get_codes()
        if codes_exception in (
            "jeton_invalide",
            "jeton_non_autorise",
            "email_deja_utilise",
            "changement_mot_de_passe_requis",
            "auto_modification_role_interdite",
            "dernier_administrateur",
            "auto_desactivation_interdite",
            "compte_deja_desactive",
            "ancien_mot_de_passe_incorrect",
        ):
            return codes_exception

    correspondances = {
        status.HTTP_401_UNAUTHORIZED: "non_authentifie",
        status.HTTP_403_FORBIDDEN: "acces_interdit",
        status.HTTP_404_NOT_FOUND: "introuvable",
        status.HTTP_405_METHOD_NOT_ALLOWED: "methode_non_autorisee",
        status.HTTP_429_TOO_MANY_REQUESTS: "trop_de_requetes",
    }
    if code_http in correspondances:
        if code_http == status.HTTP_401_UNAUTHORIZED and isinstance(
            exception,
            exceptions.AuthenticationFailed,
        ):
            code_authentification = exception.get_codes()
            if code_authentification == "identifiants_invalides":
                return code_authentification
            if code_authentification in ("jeton_invalide", "jeton_expire"):
                return code_authentification
            if _detail_contient_texte(exception.detail, "user_inactive") or (
                _detail_contient_texte(exception.detail, "user_not_found")
                or _contient_code(code_authentification, "token_not_valid")
            ):
                if _detail_contient_expiration(exception.detail):
                    return "jeton_expire"
                return "jeton_invalide"
        return correspondances[code_http]

    if isinstance(
        exception,
        (exceptions.ParseError, exceptions.UnsupportedMediaType),
    ):
        return "donnees_invalides"

    if isinstance(exception, exceptions.ValidationError):
        if _contient_code(exception.get_codes(), "champs_inconnus"):
            return "champs_inconnus"
        return "donnees_invalides"

    return "erreur"


def _contient_code(codes: Any, code_recherche: str) -> bool:
    if isinstance(codes, dict):
        return any(_contient_code(code, code_recherche) for code in codes.values())
    if isinstance(codes, (list, tuple)):
        return any(_contient_code(code, code_recherche) for code in codes)
    return codes == code_recherche


def _detail_contient_expiration(detail: Any) -> bool:
    if isinstance(detail, dict):
        return any(_detail_contient_expiration(valeur) for valeur in detail.values())
    if isinstance(detail, (list, tuple)):
        return any(_detail_contient_expiration(valeur) for valeur in detail)
    return isinstance(detail, str) and "expired" in detail.casefold()


def _detail_contient_texte(detail: Any, texte: str) -> bool:
    if isinstance(detail, dict):
        return any(_detail_contient_texte(valeur, texte) for valeur in detail.values())
    if isinstance(detail, (list, tuple)):
        return any(_detail_contient_texte(valeur, texte) for valeur in detail)
    return isinstance(detail, str) and detail.casefold() == texte.casefold()


def _detail_francais(exception: Exception, donnees: Any) -> str:
    if (
        isinstance(exception, exceptions.PermissionDenied)
        and exception.get_codes() == "changement_mot_de_passe_requis"
    ):
        return "Un changement de mot de passe est requis."
    if (
        isinstance(exception, exceptions.PermissionDenied)
        and exception.get_codes() == "auto_modification_role_interdite"
    ):
        return "Un administrateur ne peut pas modifier son propre rôle."
    if (
        isinstance(exception, exceptions.PermissionDenied)
        and exception.get_codes() == "auto_desactivation_interdite"
    ):
        return "Un administrateur ne peut pas se désactiver lui-même."
    if (
        isinstance(exception, exceptions.APIException)
        and exception.get_codes() == "dernier_administrateur"
        and "désactiv" in str(exception.detail)
    ):
        return "Le dernier administrateur actif ne peut pas être désactivé."
    if (
        isinstance(exception, exceptions.APIException)
        and exception.get_codes() == "compte_deja_desactive"
    ):
        return "Ce compte est déjà désactivé."

    if (
        isinstance(exception, exceptions.AuthenticationFailed)
        and exception.get_codes() == "identifiants_invalides"
    ):
        return "E-mail ou mot de passe incorrect."
    if isinstance(exception, exceptions.AuthenticationFailed):
        if exception.get_codes() == "jeton_expire":
            return "Le jeton de rafraîchissement a expiré."
        if _detail_contient_expiration(exception.detail):
            return "Le jeton d’accès a expiré."
        if exception.get_codes() == "jeton_invalide":
            return "Le jeton de rafraîchissement est invalide."
        if _detail_contient_texte(exception.detail, "user_inactive"):
            return "Le jeton d’accès est invalide."
        if _contient_code(exception.get_codes(), "token_not_valid") or _detail_contient_texte(
            exception.detail,
            "user_not_found",
        ):
            return "Le jeton d’accès est invalide."

    messages = {
        exceptions.NotAuthenticated: "Authentification requise.",
        exceptions.AuthenticationFailed: "Authentification refusée.",
        exceptions.PermissionDenied: "Accès interdit.",
        exceptions.NotFound: "Ressource introuvable.",
        exceptions.MethodNotAllowed: "Méthode non autorisée.",
        exceptions.Throttled: "Trop de requêtes. Réessayez après le délai indiqué.",
        exceptions.ParseError: "Le corps JSON est invalide.",
        exceptions.UnsupportedMediaType: "Le type de contenu n’est pas pris en charge.",
    }
    for type_exception, message in messages.items():
        if isinstance(exception, type_exception):
            return message

    detail = donnees.get("detail") if isinstance(donnees, dict) else None
    if detail is None:
        return "Une erreur est survenue."
    return str(detail)
