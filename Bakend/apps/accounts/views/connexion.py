"""Vues publiques d’authentification."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.exemples_json import (
    exemple_requete_openapi_connexion,
    exemples_openapi_connexion,
)
from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import TypeEvenementSecurite
from apps.accounts.serializers.connexion import (
    ConnexionSerializer,
    ErreurSerializer,
    ErreurValidationSerializer,
    ReponseConnexionSerializer,
    UtilisateurResumeConnexionSerializer,
)
from apps.accounts.services import authentifier_utilisateur
from apps.accounts.throttling import ConnexionParAdresseIP, ConnexionParEmail


class ConnexionVue(APIView):
    """Authentifie un compte et délivre une paire JWT."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (ConnexionParAdresseIP, ConnexionParEmail)

    @extend_schema(
        tags=["Authentification"],
        summary="Ouvrir une session avec une paire JWT",
        description=(
            "Accès public. Les tentatives sont limitées par adresse IP et par e-mail "
            "normalisé, y compris si aucun compte ne correspond. Les réponses portent "
            "Cache-Control: no-store et Pragma: no-cache. Un 401 inclut "
            "WWW-Authenticate: Bearer; un 429 inclut Retry-After en secondes."
        ),
        operation_id="authentifier_utilisateur",
        request=ConnexionSerializer,
        examples=[exemple_requete_openapi_connexion()],
        responses={
            200: OpenApiResponse(
                ReponseConnexionSerializer,
                description="Connexion réussie. Cache-Control: no-store.",
                examples=exemples_openapi_connexion("succes"),
            ),
            400: OpenApiResponse(
                ErreurValidationSerializer,
                description="Entrée invalide, JSON malformé ou champ inconnu.",
                examples=exemples_openapi_connexion(
                    "validation",
                    "champs_inconnus",
                    "json_malforme",
                ),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description=(
                    "Identifiants incorrects. En-têtes WWW-Authenticate: Bearer "
                    "et Cache-Control: no-store."
                ),
                examples=exemples_openapi_connexion("identifiants_invalides"),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée. Cache-Control: no-store.",
                examples=exemples_openapi_connexion("methode_non_autorisee"),
            ),
            415: OpenApiResponse(
                ErreurValidationSerializer,
                description="Type de contenu non pris en charge.",
                examples=exemples_openapi_connexion("type_contenu_non_pris_en_charge"),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite de débit atteinte; Retry-After est exprimé en secondes.",
                examples=exemples_openapi_connexion("trop_de_requetes"),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_connexion("erreur_interne"),
            ),
        },
        auth=[],
    )
    def post(self, requete):
        """Valide les identifiants puis renvoie les jetons et le résumé du compte."""
        erreur_analyse = getattr(self, "erreur_analyse_connexion", None)
        if erreur_analyse is not None:
            raise erreur_analyse

        serializer = ConnexionSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        utilisateur, jetons = authentifier_utilisateur(
            serializer.validated_data["email"],
            serializer.validated_data["mot_de_passe"],
            requete._request,
        )
        resume = UtilisateurResumeConnexionSerializer(utilisateur).data
        return Response(
            {
                **jetons,
                "utilisateur": resume,
            },
            status=status.HTTP_200_OK,
        )

    def get_authenticate_header(self, requete):
        """Conserve le challenge Bearer sans authentifier les requêtes publiques."""
        return "Bearer"

    def handle_exception(self, exception):
        """Journalise les erreurs d’entrée, de méthode et de limitation sans les secrets."""
        raisons = (
            (exceptions.ValidationError, "donnees_invalides"),
            (exceptions.ParseError, "json_malforme"),
            (exceptions.UnsupportedMediaType, "type_contenu_invalide"),
            (exceptions.MethodNotAllowed, "methode_non_autorisee"),
            (exceptions.Throttled, "limitation_debit"),
            (exceptions.PermissionDenied, "acces_interdit"),
            (exceptions.NotAuthenticated, "non_authentifie"),
        )
        raison_echec = next(
            (raison for type_exception, raison in raisons if isinstance(exception, type_exception)),
            "erreur_interne",
        )
        if not isinstance(exception, exceptions.AuthenticationFailed):
            journaliser_evenement(
                self.request._request,
                TypeEvenementSecurite.CONNEXION_ECHOUEE,
                details={"raison": raison_echec},
                obligatoire=True,
            )
        return super().handle_exception(exception)
