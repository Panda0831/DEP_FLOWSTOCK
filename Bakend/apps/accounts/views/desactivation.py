"""Désactivation administrative d’un compte utilisateur."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.exemples_json import exemples_openapi_desactivation_utilisateur
from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import TypeEvenementSecurite
from apps.accounts.permissions import ChangementMotDePasseNonRequis, EstAdministrateur
from apps.accounts.serializers.connexion import ErreurSerializer, ErreurValidationSerializer
from apps.accounts.serializers.utilisateurs import UtilisateurAdminSerializer
from apps.accounts.services import desactiver_utilisateur_par_administrateur


class DesactivationUtilisateurVue(APIView):
    """Désactive un compte sans supprimer ses données."""

    permission_classes = (
        IsAuthenticated,
        ChangementMotDePasseNonRequis,
        EstAdministrateur,
    )

    @extend_schema(
        tags=["Utilisateurs"],
        summary="Désactiver un utilisateur",
        description=(
            "Réservé aux administrateurs. Cette action ne reçoit aucun corps, conserve "
            "les données du compte, révoque ses jetons de rafraîchissement et est "
            "journalisée. Un compte déjà inactif ne peut pas être désactivé à nouveau."
        ),
        operation_id="desactiver_utilisateur",
        request=None,
        responses={
            200: OpenApiResponse(
                UtilisateurAdminSerializer,
                description="Compte désactivé et jetons de rafraîchissement révoqués.",
                examples=exemples_openapi_desactivation_utilisateur("desactivation_succes"),
            ),
            400: OpenApiResponse(
                ErreurValidationSerializer,
                description="Un corps interdit a été fourni.",
                examples=exemples_openapi_desactivation_utilisateur(
                    "desactivation_corps_interdit",
                ),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description="Jeton d’accès absent, invalide ou expiré.",
                examples=exemples_openapi_desactivation_utilisateur(
                    "desactivation_non_authentifie",
                    "desactivation_jeton_invalide",
                    "desactivation_jeton_expire",
                ),
            ),
            403: OpenApiResponse(
                ErreurSerializer,
                description="Rôle insuffisant ou auto-désactivation interdite.",
                examples=exemples_openapi_desactivation_utilisateur(
                    "desactivation_acces_interdit",
                    "desactivation_changement_mot_de_passe_requis",
                    "desactivation_auto_interdite",
                ),
            ),
            404: OpenApiResponse(
                ErreurSerializer,
                description="UUID mal formé ou compte inexistant.",
                examples=exemples_openapi_desactivation_utilisateur(
                    "desactivation_uuid_invalide",
                    "desactivation_utilisateur_introuvable",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_desactivation_utilisateur(
                    "desactivation_methode_interdite",
                ),
            ),
            409: OpenApiResponse(
                ErreurSerializer,
                description="Dernier administrateur actif ou compte déjà désactivé.",
                examples=exemples_openapi_desactivation_utilisateur(
                    "desactivation_dernier_administrateur",
                    "desactivation_deja_inactif",
                ),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite générale de requêtes atteinte.",
                examples=exemples_openapi_desactivation_utilisateur(
                    "desactivation_limite_atteinte",
                ),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_desactivation_utilisateur(
                    "desactivation_erreur_interne",
                ),
            ),
        },
    )
    def post(self, requete, uuid):
        """Désactive un compte cible après validation de l’absence de corps."""
        if requete._request.body.strip():
            raise exceptions.ValidationError(
                {"corps": ["Cette route n’accepte pas de corps."]},
            )

        utilisateur = desactiver_utilisateur_par_administrateur(
            uuid,
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
        """Journalise les refus sans enregistrer le corps ni de données sensibles."""
        if isinstance(exception, exceptions.ValidationError):
            raison = "corps_interdit"
        elif isinstance(exception, exceptions.PermissionDenied):
            raison = str(exception.get_codes())
        elif isinstance(exception, exceptions.NotFound):
            raison = "introuvable"
        elif isinstance(exception, exceptions.MethodNotAllowed):
            raison = "methode_non_autorisee"
        elif isinstance(exception, exceptions.Throttled):
            raison = "limitation_debit"
        elif isinstance(exception, exceptions.AuthenticationFailed):
            raison = str(exception.get_codes())
        elif isinstance(exception, exceptions.NotAuthenticated):
            raison = "non_authentifie"
        elif isinstance(exception, exceptions.APIException):
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
