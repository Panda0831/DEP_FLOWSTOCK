"""Vues publiques de renouvellement des jetons."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.exemples_json import (
    exemple_requete_openapi_rafraichissement,
    exemples_openapi_rafraichissement,
)
from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import TypeEvenementSecurite
from apps.accounts.serializers.connexion import ErreurSerializer, ErreurValidationSerializer
from apps.accounts.serializers.jetons import (
    RafraichissementSerializer,
    ReponseRafraichissementSerializer,
)
from apps.accounts.services import EchecRafraichissement, rafraichir_jetons
from apps.accounts.throttling import RafraichissementParAdresseIP


class RafraichissementJetonsVue(APIView):
    """Valide et fait tourner un jeton de rafraîchissement encore actif."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (RafraichissementParAdresseIP,)

    @extend_schema(
        tags=["Authentification"],
        summary="Renouveler et faire tourner une paire JWT",
        description=(
            "Accès public avec un jeton refresh valide. Le refresh présenté est "
            "révoqué dans la même transaction que l’émission de la nouvelle paire. "
            "Les jetons révoqués, expirés, de type access ou associés à un compte "
            "inactif sont refusés. Les échecs sont journalisés sans enregistrer le "
            "jeton. Les réponses portent Cache-Control: no-store; les 401 incluent "
            "WWW-Authenticate: Bearer et les 429 Retry-After."
        ),
        operation_id="rafraichir_jetons",
        request=RafraichissementSerializer,
        examples=[exemple_requete_openapi_rafraichissement()],
        responses={
            200: OpenApiResponse(
                ReponseRafraichissementSerializer,
                description="Nouvelle paire JWT; l’ancien refresh est révoqué.",
                examples=exemples_openapi_rafraichissement("rafraichissement_succes"),
            ),
            400: OpenApiResponse(
                ErreurValidationSerializer,
                description="Entrée invalide, JSON malformé ou champ inconnu.",
                examples=exemples_openapi_rafraichissement(
                    "rafraichissement_validation",
                    "rafraichissement_champs_inconnus",
                    "rafraichissement_json_malforme",
                ),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description=("Jeton invalide, révoqué ou expiré. WWW-Authenticate: Bearer."),
                examples=exemples_openapi_rafraichissement(
                    "rafraichissement_jeton_invalide",
                    "rafraichissement_jeton_expire",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_rafraichissement(
                    "rafraichissement_methode_interdite",
                ),
            ),
            415: OpenApiResponse(
                ErreurValidationSerializer,
                description="Type de contenu non pris en charge.",
                examples=exemples_openapi_rafraichissement("rafraichissement_type_contenu"),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite de débit atteinte; Retry-After est exprimé en secondes.",
                examples=exemples_openapi_rafraichissement("rafraichissement_limite_atteinte"),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_rafraichissement(
                    "rafraichissement_erreur_interne",
                ),
            ),
        },
        auth=[],
    )
    def post(self, requete):
        """Valide le refresh et retourne une nouvelle paire de jetons."""
        serializer = RafraichissementSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        jetons = rafraichir_jetons(serializer.validated_data["refresh"])
        return Response(jetons, status=status.HTTP_200_OK)

    def get_authenticate_header(self, requete):
        """Fournit un challenge Bearer pour conserver les erreurs 401."""
        return "Bearer"

    def handle_exception(self, exception):
        """Journalise chaque échec du renouvellement sans y inclure le refresh."""
        if isinstance(exception, EchecRafraichissement):
            raison = exception.raison_interne
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
        else:
            raison = "erreur_interne"

        journaliser_evenement(
            self.request._request,
            TypeEvenementSecurite.JETON_REJETE,
            details={"raison": raison},
            obligatoire=True,
        )
        return super().handle_exception(exception)
