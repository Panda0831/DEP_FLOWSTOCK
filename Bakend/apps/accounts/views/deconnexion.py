"""Vue authentifiée de révocation du jeton de rafraîchissement courant."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.exemples_json import (
    exemple_requete_openapi_deconnexion,
    exemples_openapi_deconnexion,
)
from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import TypeEvenementSecurite
from apps.accounts.permissions import ChangementMotDePasseNonRequis
from apps.accounts.serializers.connexion import ErreurSerializer, ErreurValidationSerializer
from apps.accounts.serializers.jetons import DeconnexionSerializer
from apps.accounts.services import EchecDeconnexion, deconnecter_utilisateur
from apps.accounts.throttling import DeconnexionParAdresseIP


class DeconnexionVue(APIView):
    """Révoque le refresh fourni après en avoir vérifié le propriétaire."""

    permission_classes = (IsAuthenticated, ChangementMotDePasseNonRequis)
    throttle_classes = (DeconnexionParAdresseIP,)

    @extend_schema(
        tags=["Authentification"],
        summary="Révoquer le jeton de rafraîchissement",
        description=(
            "Exige un jeton d’accès valide et un jeton de rafraîchissement appartenant "
            "au même compte. La révocation est idempotente. Les tentatives sont limitées "
            "par adresse IP; les succès et refus sont journalisés sans enregistrer le jeton."
        ),
        operation_id="deconnecter_utilisateur",
        request=DeconnexionSerializer,
        examples=[exemple_requete_openapi_deconnexion()],
        responses={
            204: OpenApiResponse(description="Jeton révoqué; aucun corps de réponse."),
            400: OpenApiResponse(
                ErreurValidationSerializer,
                description="Corps invalide ou jeton de rafraîchissement mal formé.",
                examples=exemples_openapi_deconnexion(
                    "deconnexion_validation",
                    "deconnexion_champs_inconnus",
                    "deconnexion_json_malforme",
                    "deconnexion_jeton_invalide",
                ),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description="Jeton d’accès absent, invalide ou expiré.",
                examples=exemples_openapi_deconnexion(
                    "deconnexion_non_authentifie",
                    "deconnexion_acces_invalide",
                    "deconnexion_acces_expire",
                ),
            ),
            403: OpenApiResponse(
                ErreurSerializer,
                description="Le jeton de rafraîchissement appartient à un autre compte.",
                examples=exemples_openapi_deconnexion("deconnexion_jeton_non_autorise"),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_deconnexion("deconnexion_methode_interdite"),
            ),
            415: OpenApiResponse(
                ErreurValidationSerializer,
                description="Type de contenu non pris en charge.",
                examples=exemples_openapi_deconnexion("deconnexion_type_contenu"),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite de débit atteinte; Retry-After est exprimé en secondes.",
                examples=exemples_openapi_deconnexion("deconnexion_limite_atteinte"),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_deconnexion("deconnexion_erreur_interne"),
            ),
        },
    )
    def post(self, requete):
        """Valide et révoque le refresh sans retourner de contenu."""
        serializer = DeconnexionSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        deconnecter_utilisateur(
            serializer.validated_data["refresh"],
            requete.user,
            requete._request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_authenticate_header(self, requete):
        """Fournit un challenge Bearer pour les réponses 401."""
        return "Bearer"

    def handle_exception(self, exception):
        """Journalise les refus sans enregistrer de jeton ni de donnée brute."""
        if isinstance(exception, EchecDeconnexion):
            raison = "jeton_invalide"
        elif isinstance(exception, exceptions.PermissionDenied):
            raison = "jeton_non_autorise"
        elif isinstance(exception, exceptions.ValidationError):
            raison = "donnees_invalides"
        elif isinstance(exception, exceptions.ParseError):
            raison = "json_malforme"
        elif isinstance(exception, exceptions.UnsupportedMediaType):
            raison = "type_contenu_invalide"
        elif isinstance(exception, exceptions.MethodNotAllowed):
            raison = "methode_non_autorisee"
        elif isinstance(exception, exceptions.Throttled):
            raison = "limitation_debit"
        elif isinstance(exception, exceptions.NotAuthenticated):
            raison = "non_authentifie"
        else:
            raison = "erreur_interne"

        utilisateur = self.request.user
        journaliser_evenement(
            self.request._request,
            TypeEvenementSecurite.ACCES_REFUSE,
            utilisateur=utilisateur if utilisateur.is_authenticated else None,
            details={"raison": raison},
            obligatoire=True,
        )
        return super().handle_exception(exception)
