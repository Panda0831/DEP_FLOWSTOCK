"""Vue de consultation du profil authentifié."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.exemples_json import (
    exemple_requete_openapi_modification_profil,
    exemples_openapi_modification_profil,
    exemples_openapi_profil,
)
from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import TypeEvenementSecurite
from apps.accounts.permissions import ChangementMotDePasseNonRequis
from apps.accounts.serializers.connexion import ErreurSerializer, ErreurValidationSerializer
from apps.accounts.serializers.profil import ProfilModificationSerializer, ProfilSerializer
from apps.accounts.services import modifier_profil_utilisateur
from apps.accounts.throttling import ProfilParUtilisateur


class MonProfilVue(APIView):
    """Retourne uniquement les champs publics du compte authentifié."""

    permission_classes = (IsAuthenticated, ChangementMotDePasseNonRequis)
    throttle_classes = (ProfilParUtilisateur,)

    @extend_schema(
        tags=["Authentification"],
        summary="Consulter le profil du compte authentifié",
        description=(
            "Requiert un jeton Bearer d’accès valide. Cette lecture reste autorisée "
            "si un changement de mot de passe est requis. La réponse ne contient "
            "aucun identifiant interne, hash de mot de passe ou indicateur superutilisateur. "
            "Cache-Control: no-store est appliqué."
        ),
        operation_id="consulter_mon_profil",
        responses={
            200: OpenApiResponse(
                ProfilSerializer,
                description="Profil du titulaire du jeton.",
                examples=exemples_openapi_profil("profil_succes", "profil_sans_connexion"),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description="Jeton absent, expiré ou invalide.",
                examples=exemples_openapi_profil(
                    "profil_non_authentifie",
                    "profil_jeton_expire",
                    "profil_jeton_invalide",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_profil("profil_methode_interdite"),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite générale de débit atteinte.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_limite_atteinte",
                ),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_erreur_interne",
                ),
            ),
        },
    )
    def get(self, requete):
        """Sérialise le compte authentifié selon sa liste blanche de champs."""
        return Response(ProfilSerializer(requete.user).data)

    @extend_schema(
        tags=["Authentification"],
        summary="Modifier les champs autorisés du profil connecté",
        description=(
            "Requiert un jeton Bearer et un changement de mot de passe déjà effectué. "
            "Seuls nom, prenom et telephone sont modifiables; email, role et les champs "
            "internes sont refusés. Les modifications sont journalisées. La réponse "
            "est protégée contre la mise en cache."
        ),
        operation_id="modifier_mon_profil",
        request=ProfilModificationSerializer,
        examples=[exemple_requete_openapi_modification_profil()],
        responses={
            200: OpenApiResponse(
                ProfilSerializer,
                description="Profil actualisé.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_succes",
                ),
            ),
            400: OpenApiResponse(
                ErreurValidationSerializer,
                description="Donnée invalide, JSON malformé ou champ interdit.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_validation",
                    "profil_modification_champs_inconnus",
                    "profil_modification_json_malforme",
                ),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description="Jeton Bearer absent, invalide ou expiré.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_non_authentifie",
                    "profil_modification_jeton_invalide",
                    "profil_modification_jeton_expire",
                ),
            ),
            403: OpenApiResponse(
                ErreurSerializer,
                description="Changement du mot de passe requis avant la modification.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_changement_mot_de_passe_requis",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_methode_interdite",
                ),
            ),
            415: OpenApiResponse(
                ErreurValidationSerializer,
                description="Type de contenu non pris en charge.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_type_contenu",
                ),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite générale de débit atteinte.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_limite_atteinte",
                ),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_modification_profil(
                    "profil_modification_erreur_interne",
                ),
            ),
        },
    )
    def patch(self, requete):
        """Valide et enregistre uniquement les champs personnels autorisés."""
        serializer = ProfilModificationSerializer(data=requete.data, partial=True)
        serializer.is_valid(raise_exception=True)
        utilisateur = modifier_profil_utilisateur(
            requete.user.pk,
            serializer.validated_data,
            requete._request,
        )
        return Response(ProfilSerializer(utilisateur).data, status=status.HTTP_200_OK)

    def handle_exception(self, exception):
        """Journalise les refus sans inclure les données de profil reçues."""
        utilisateur = getattr(self.request, "user", None)
        utilisateur = utilisateur if utilisateur and utilisateur.is_authenticated else None
        raison = (
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
        journaliser_evenement(
            self.request._request,
            TypeEvenementSecurite.ACCES_REFUSE,
            utilisateur=utilisateur,
            details={"raison": raison},
            obligatoire=True,
        )
        return super().handle_exception(exception)
