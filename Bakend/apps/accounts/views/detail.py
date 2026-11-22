"""Consultation administrative d’un compte utilisateur."""

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import exceptions
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.accounts.exemples_json import (
    EXEMPLE_REQUETE_MODIFICATION_UTILISATEUR,
    exemples_openapi_detail_utilisateur,
    exemples_openapi_modification_utilisateur,
)
from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import TypeEvenementSecurite, Utilisateur
from apps.accounts.permissions import ChangementMotDePasseNonRequis, EstAdministrateur
from apps.accounts.serializers.connexion import ErreurSerializer, ErreurValidationSerializer
from apps.accounts.serializers.utilisateurs import (
    UtilisateurAdminSerializer,
    UtilisateurModificationSerializer,
)
from apps.accounts.services import (
    ConflitEmail,
    modifier_utilisateur_par_administrateur,
)


class DetailUtilisateurVue(APIView):
    """Retourne les champs administratifs autorisés d’un compte ciblé."""

    permission_classes = (
        IsAuthenticated,
        ChangementMotDePasseNonRequis,
        EstAdministrateur,
    )
    throttle_classes = (UserRateThrottle,)

    @extend_schema(
        tags=["Utilisateurs"],
        summary="Consulter un utilisateur",
        description=(
            "Réservé aux administrateurs authentifiés n’ayant pas à changer leur mot "
            "de passe. Seuls les champs de la liste blanche administrateur sont renvoyés."
        ),
        operation_id="consulter_utilisateur",
        parameters=[
            OpenApiParameter(
                "uuid",
                str,
                location=OpenApiParameter.PATH,
                description="UUID du compte utilisateur.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                UtilisateurAdminSerializer,
                description="Compte trouvé; aucun champ d’authentification n’est exposé.",
                examples=exemples_openapi_detail_utilisateur("detail_succes"),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description="Jeton d’accès absent, invalide ou expiré.",
                examples=exemples_openapi_detail_utilisateur(
                    "detail_non_authentifie",
                    "detail_jeton_invalide",
                    "detail_jeton_expire",
                ),
            ),
            403: OpenApiResponse(
                ErreurSerializer,
                description="Rôle insuffisant ou changement de mot de passe requis.",
                examples=exemples_openapi_detail_utilisateur(
                    "detail_acces_interdit",
                    "detail_changement_mot_de_passe_requis",
                ),
            ),
            404: OpenApiResponse(
                ErreurSerializer,
                description="UUID mal formé ou compte inexistant.",
                examples=exemples_openapi_detail_utilisateur(
                    "detail_uuid_invalide",
                    "detail_utilisateur_introuvable",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_detail_utilisateur("detail_methode_interdite"),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite générale de requêtes atteinte.",
                examples=exemples_openapi_detail_utilisateur("detail_limite_atteinte"),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_detail_utilisateur("detail_erreur_interne"),
            ),
        },
    )
    def get(self, requete, uuid):
        """Retourne un compte ou une erreur uniforme 404."""
        try:
            utilisateur = Utilisateur.objects.get(uuid=uuid)
        except Utilisateur.DoesNotExist as erreur:
            raise NotFound() from erreur

        journaliser_evenement(
            requete._request,
            TypeEvenementSecurite.UTILISATEUR_CONSULTE,
            utilisateur=requete.user,
            utilisateur_cible=utilisateur,
            obligatoire=True,
        )
        reponse = Response(UtilisateurAdminSerializer(utilisateur).data)
        reponse["Cache-Control"] = "no-store"
        reponse["Pragma"] = "no-cache"
        return reponse

    @extend_schema(
        tags=["Utilisateurs"],
        summary="Modifier un utilisateur",
        description=(
            "Réservé aux administrateurs. Seuls email, nom, prenom, telephone et role "
            "sont modifiables. PUT et toute affectation de masse sont interdits. Les "
            "changements d’e-mail ou de rôle révoquent les jetons de rafraîchissement."
        ),
        operation_id="modifier_utilisateur",
        request=UtilisateurModificationSerializer,
        examples=[
            OpenApiExample(
                name="Modification partielle d’un utilisateur",
                value=EXEMPLE_REQUETE_MODIFICATION_UTILISATEUR,
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                UtilisateurAdminSerializer,
                description="Compte modifié ou inchangé si le corps est vide.",
                examples=exemples_openapi_modification_utilisateur("modification_succes"),
            ),
            400: OpenApiResponse(
                ErreurValidationSerializer,
                description="Données invalides ou champ non autorisé.",
                examples=exemples_openapi_modification_utilisateur(
                    "modification_validation",
                    "modification_champs_inconnus",
                    "modification_json_malforme",
                ),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description="Jeton d’accès absent, invalide ou expiré.",
                examples=exemples_openapi_modification_utilisateur(
                    "modification_non_authentifie",
                    "modification_jeton_invalide",
                    "modification_jeton_expire",
                ),
            ),
            403: OpenApiResponse(
                ErreurSerializer,
                description=(
                    "Rôle insuffisant, changement de mot de passe requis ou auto-modification."
                ),
                examples=exemples_openapi_modification_utilisateur(
                    "modification_acces_interdit",
                    "modification_changement_mot_de_passe_requis",
                    "modification_role_propre_interdit",
                ),
            ),
            404: OpenApiResponse(
                ErreurSerializer,
                description="UUID mal formé ou compte inexistant.",
                examples=exemples_openapi_modification_utilisateur(
                    "modification_uuid_invalide",
                    "modification_utilisateur_introuvable",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée; PUT est interdit.",
                examples=exemples_openapi_modification_utilisateur(
                    "modification_methode_interdite"
                ),
            ),
            409: OpenApiResponse(
                ErreurSerializer,
                description="E-mail en conflit ou dernier administrateur actif.",
                examples=exemples_openapi_modification_utilisateur(
                    "modification_email_conflit",
                    "modification_dernier_administrateur",
                ),
            ),
            415: OpenApiResponse(
                ErreurValidationSerializer,
                description="Type de contenu non pris en charge.",
                examples=exemples_openapi_modification_utilisateur("modification_type_contenu"),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite générale de requêtes atteinte.",
                examples=exemples_openapi_modification_utilisateur("modification_limite_atteinte"),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_modification_utilisateur("modification_erreur_interne"),
            ),
        },
    )
    def patch(self, requete, uuid):
        """Valide les champs de modification puis délègue au service transactionnel."""
        serializer = UtilisateurModificationSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        utilisateur = modifier_utilisateur_par_administrateur(
            uuid,
            serializer.validated_data,
            requete.user,
            requete._request,
        )
        reponse = Response(UtilisateurAdminSerializer(utilisateur).data)
        reponse["Cache-Control"] = "no-store"
        reponse["Pragma"] = "no-cache"
        return reponse

    def get_authenticate_header(self, requete):
        """Fournit un challenge Bearer pour les réponses 401."""
        return "Bearer"

    def handle_exception(self, exception):
        """Journalise les refus sans enregistrer de données personnelles ou secrètes."""
        if isinstance(exception, ConflitEmail):
            raison = "email_deja_utilise"
        elif isinstance(exception, exceptions.ValidationError):
            raison = "donnees_invalides"
        elif isinstance(exception, exceptions.PermissionDenied):
            raison = str(exception.get_codes())
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
        elif isinstance(exception, NotFound):
            raison = "introuvable"
        elif isinstance(exception, exceptions.AuthenticationFailed):
            raison = str(exception.get_codes())
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


@extend_schema(exclude=True)
class UUIDUtilisateurInvalideVue(APIView):
    """Fournit une erreur JSON cohérente pour les UUID mal formés."""

    permission_classes = (AllowAny,)

    def get(self, requete, uuid):
        """Refuse le segment invalide sans révéler d’information sur les comptes."""
        raise NotFound()

    def patch(self, requete, uuid):
        """Refuse les UUID mal formés pour la modification."""
        raise NotFound()

    def post(self, requete, uuid):
        """Refuse les UUID mal formés pour la désactivation."""
        raise NotFound()

    def handle_exception(self, exception):
        """Journalise les tentatives avec un identifiant mal formé."""
        journaliser_evenement(
            self.request._request,
            TypeEvenementSecurite.ACCES_REFUSE,
            utilisateur=(self.request.user if self.request.user.is_authenticated else None),
            details={"raison": "introuvable"},
            obligatoire=True,
        )
        return super().handle_exception(exception)
