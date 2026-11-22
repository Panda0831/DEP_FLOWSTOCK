"""Vues de changement et de réinitialisation des mots de passe."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.exemples_json import (
    exemple_requete_openapi_changement_mot_de_passe,
    exemple_requete_openapi_confirmation_reinitialisation,
    exemple_requete_openapi_demande_reinitialisation,
    exemples_openapi_changement_mot_de_passe,
    exemples_openapi_confirmation_reinitialisation,
    exemples_openapi_demande_reinitialisation,
)
from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import TypeEvenementSecurite
from apps.accounts.serializers.connexion import (
    ErreurOuValidationSerializer,
    ErreurSerializer,
    ErreurValidationSerializer,
)
from apps.accounts.serializers.mot_de_passe import (
    ChangementMotDePasseSerializer,
    ConfirmationReinitialisationSerializer,
    DemandeReinitialisationSerializer,
)
from apps.accounts.services import (
    LienReinitialisationInvalide,
    changer_mot_de_passe_utilisateur,
    confirmer_reinitialisation_mot_de_passe,
    demander_reinitialisation_mot_de_passe,
)
from apps.accounts.throttling import (
    ChangementMotDePasseParUtilisateur,
    ConfirmationReinitialisationParAdresseIP,
    ReinitialisationParAdresseIP,
    ReinitialisationParEmail,
)


class _VueMotDePasse(APIView):
    """Journalise les erreurs sans enregistrer de mot de passe ni de jeton."""

    evenement_echec = TypeEvenementSecurite.ACCES_REFUSE

    def handle_exception(self, exception):
        """Consigne uniquement une raison interne non sensible avant la réponse API."""
        utilisateur = getattr(self.request, "user", None)
        utilisateur = utilisateur if utilisateur and utilisateur.is_authenticated else None
        evenement = (
            TypeEvenementSecurite.JETON_REJETE
            if isinstance(exception, LienReinitialisationInvalide)
            else self.evenement_echec
        )
        raison = (
            "jeton_invalide"
            if evenement == TypeEvenementSecurite.JETON_REJETE
            else (
                "limitation_debit"
                if isinstance(exception, exceptions.Throttled)
                else "donnees_invalides"
                if isinstance(
                    exception,
                    (
                        exceptions.ValidationError,
                        exceptions.ParseError,
                        exceptions.UnsupportedMediaType,
                    ),
                )
                else "acces_refuse"
            )
        )
        journaliser_evenement(
            self.request._request,
            evenement,
            utilisateur=utilisateur,
            details={"raison": raison},
            obligatoire=True,
        )
        return super().handle_exception(exception)


class ChangementMotDePasseVue(_VueMotDePasse):
    """Change le mot de passe du compte actuellement authentifié."""

    permission_classes = (IsAuthenticated,)
    throttle_classes = (ChangementMotDePasseParUtilisateur,)

    @extend_schema(
        tags=["Authentification"],
        summary="Changer le mot de passe du compte connecté",
        description=(
            "Requiert un jeton Bearer. Autorisé même si le compte doit changer son mot "
            "de passe. Le nouveau mot de passe est validé avec les validateurs Django; "
            "tous les jetons de rafraîchissement sont révoqués après succès. La réponse "
            "est non mise en cache et la limite est de 5 tentatives par heure et par compte."
        ),
        operation_id="changer_mot_de_passe",
        request=ChangementMotDePasseSerializer,
        examples=[exemple_requete_openapi_changement_mot_de_passe()],
        responses={
            200: OpenApiResponse(
                ErreurSerializer,
                description="Mot de passe modifié; reconnexion nécessaire.",
                examples=exemples_openapi_changement_mot_de_passe("changement_succes"),
            ),
            400: OpenApiResponse(
                ErreurOuValidationSerializer,
                description="Ancien secret incorrect, données invalides ou champ inconnu.",
                examples=exemples_openapi_changement_mot_de_passe(
                    "changement_ancien_incorrect",
                    "changement_validation",
                    "changement_confirmation_invalide",
                    "changement_mot_de_passe_identique",
                    "changement_champs_inconnus",
                    "changement_json_malforme",
                ),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description="Jeton Bearer absent, invalide ou expiré.",
                examples=exemples_openapi_changement_mot_de_passe(
                    "changement_non_authentifie",
                    "changement_jeton_invalide",
                    "changement_jeton_expire",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_changement_mot_de_passe(
                    "changement_methode_interdite",
                ),
            ),
            415: OpenApiResponse(
                ErreurValidationSerializer,
                description="Type de contenu non pris en charge.",
                examples=exemples_openapi_changement_mot_de_passe(
                    "changement_type_contenu",
                ),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite de débit atteinte; Retry-After est exprimé en secondes.",
                examples=exemples_openapi_changement_mot_de_passe(
                    "changement_limite_atteinte",
                ),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_changement_mot_de_passe(
                    "changement_erreur_interne",
                ),
            ),
        },
    )
    def post(self, requete):
        """Vérifie l’ancien secret puis révoque toutes les sessions."""
        serializer = ChangementMotDePasseSerializer(
            data=requete.data,
            context={"request": requete},
        )
        serializer.is_valid(raise_exception=True)
        changer_mot_de_passe_utilisateur(
            requete.user.pk,
            serializer.validated_data["ancien_mot_de_passe"],
            serializer.validated_data["nouveau_mot_de_passe"],
            requete._request,
        )
        return Response(
            {"detail": "Mot de passe modifié. Veuillez vous reconnecter."},
            status=status.HTTP_200_OK,
        )


class DemandeReinitialisationMotDePasseVue(_VueMotDePasse):
    """Accepte uniformément les demandes de réinitialisation par e-mail."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (ReinitialisationParAdresseIP, ReinitialisationParEmail)

    @extend_schema(
        tags=["Authentification"],
        summary="Demander un lien de réinitialisation du mot de passe",
        description=(
            "Endpoint public. Une réponse identique est renvoyée si le compte est actif, "
            "inactif ou inconnu. Les demandes sont limitées par IP et par empreinte "
            "SHA-256 de l’e-mail normalisé. L’e-mail de réinitialisation est envoyé en "
            "arrière-plan uniquement pour un compte actif."
        ),
        operation_id="demander_reinitialisation_mot_de_passe",
        request=DemandeReinitialisationSerializer,
        examples=[exemple_requete_openapi_demande_reinitialisation()],
        responses={
            200: OpenApiResponse(
                ErreurSerializer,
                description="Réponse volontairement uniforme, sans révéler l’existence du compte.",
                examples=exemples_openapi_demande_reinitialisation(
                    "demande_reinitialisation_succes",
                ),
            ),
            400: OpenApiResponse(
                ErreurOuValidationSerializer,
                description="Adresse invalide, corps malformé ou champ inconnu.",
                examples=exemples_openapi_demande_reinitialisation(
                    "demande_reinitialisation_email_invalide",
                    "demande_reinitialisation_champs_inconnus",
                    "demande_reinitialisation_json_malforme",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_demande_reinitialisation(
                    "demande_reinitialisation_methode_interdite",
                ),
            ),
            415: OpenApiResponse(
                ErreurValidationSerializer,
                description="Type de contenu non pris en charge.",
                examples=exemples_openapi_demande_reinitialisation(
                    "demande_reinitialisation_type_contenu",
                ),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite de débit atteinte; Retry-After est exprimé en secondes.",
                examples=exemples_openapi_demande_reinitialisation(
                    "demande_reinitialisation_limite_atteinte",
                ),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_demande_reinitialisation(
                    "demande_reinitialisation_erreur_interne",
                ),
            ),
        },
        auth=[],
    )
    def post(self, requete):
        """Valide l’e-mail et exécute la demande sans réponse discriminante."""
        erreur_analyse = getattr(self, "erreur_analyse_reinitialisation", None)
        if erreur_analyse is not None:
            raise erreur_analyse
        serializer = DemandeReinitialisationSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        demander_reinitialisation_mot_de_passe(
            serializer.validated_data["email"],
            requete._request,
        )
        return Response(
            {
                "detail": (
                    "Si un compte correspond à cette adresse, un e-mail de réinitialisation "
                    "a été envoyé."
                )
            },
            status=status.HTTP_200_OK,
        )


class ConfirmationReinitialisationMotDePasseVue(_VueMotDePasse):
    """Consomme un jeton Django de réinitialisation à usage unique."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (ConfirmationReinitialisationParAdresseIP,)

    @extend_schema(
        tags=["Authentification"],
        summary="Confirmer la réinitialisation du mot de passe",
        description=(
            "Endpoint public limité par IP. UID inconnu, jeton invalide, jeton expiré "
            "et compte inactif renvoient le même 400. La validation du nouveau mot de "
            "passe ne commence qu’après la validation du jeton. En cas de succès, "
            "tous les jetons de rafraîchissement sont révoqués."
        ),
        operation_id="confirmer_reinitialisation_mot_de_passe",
        request=ConfirmationReinitialisationSerializer,
        examples=[exemple_requete_openapi_confirmation_reinitialisation()],
        responses={
            200: OpenApiResponse(
                ErreurSerializer,
                description="Mot de passe réinitialisé; reconnexion nécessaire.",
                examples=exemples_openapi_confirmation_reinitialisation(
                    "confirmation_reinitialisation_succes",
                ),
            ),
            400: OpenApiResponse(
                ErreurValidationSerializer,
                description="Lien invalide ou expiré, validation ou champ inconnu.",
                examples=exemples_openapi_confirmation_reinitialisation(
                    "confirmation_reinitialisation_jeton_invalide",
                    "confirmation_reinitialisation_validation",
                    "confirmation_reinitialisation_confirmation_invalide",
                    "confirmation_reinitialisation_champs_inconnus",
                    "confirmation_reinitialisation_json_malforme",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_confirmation_reinitialisation(
                    "confirmation_reinitialisation_methode_interdite",
                ),
            ),
            415: OpenApiResponse(
                ErreurValidationSerializer,
                description="Type de contenu non pris en charge.",
                examples=exemples_openapi_confirmation_reinitialisation(
                    "confirmation_reinitialisation_type_contenu",
                ),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite de débit atteinte; Retry-After est exprimé en secondes.",
                examples=exemples_openapi_confirmation_reinitialisation(
                    "confirmation_reinitialisation_limite_atteinte",
                ),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_confirmation_reinitialisation(
                    "confirmation_reinitialisation_erreur_interne",
                ),
            ),
        },
        auth=[],
    )
    def post(self, requete):
        """Valide le jeton avant le nouveau mot de passe, puis le consomme."""
        serializer = ConfirmationReinitialisationSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        donnees = serializer.validated_data
        confirmer_reinitialisation_mot_de_passe(
            donnees["uid"],
            donnees["token"],
            donnees["nouveau_mot_de_passe"],
            donnees["confirmation_nouveau_mot_de_passe"],
            requete._request,
        )
        return Response(
            {"detail": "Mot de passe réinitialisé. Vous pouvez vous connecter."},
            status=status.HTTP_200_OK,
        )
