"""Création administrative des comptes utilisateurs."""

from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.exemples_json import (
    exemple_requete_openapi_creation_utilisateur,
    exemples_openapi_creation_utilisateur,
    exemples_openapi_liste_utilisateurs,
)
from apps.accounts.journal import journaliser_evenement
from apps.accounts.models import TypeEvenementSecurite, Utilisateur
from apps.accounts.permissions import ChangementMotDePasseNonRequis, EstAdministrateur
from apps.accounts.serializers.connexion import ErreurSerializer, ErreurValidationSerializer
from apps.accounts.serializers.utilisateurs import (
    FiltresListeUtilisateursSerializer,
    ReponseListeUtilisateursSerializer,
    UtilisateurAdminSerializer,
    UtilisateurCreationSerializer,
)
from apps.accounts.services import ConflitEmail, creer_utilisateur_par_administrateur
from apps.accounts.throttling import CreationUtilisateurParAdministrateur
from apps.core.pagination import PaginationStandard


class CreationUtilisateurVue(APIView):
    """Crée un vendeur ou un administrateur à la demande d’un admin."""

    permission_classes = (
        IsAuthenticated,
        ChangementMotDePasseNonRequis,
        EstAdministrateur,
    )
    throttle_classes = (CreationUtilisateurParAdministrateur,)

    @extend_schema(
        tags=["Utilisateurs"],
        summary="Lister les utilisateurs",
        description=(
            "Réservé aux administrateurs. Recherche partielle dans le nom, le prénom "
            "et l’e-mail; filtres par rôle et état actif; tri strictement limité à une "
            "liste blanche. La taille de page est plafonnée à 100."
        ),
        operation_id="lister_utilisateurs",
        parameters=[
            OpenApiParameter("page", int, description="Numéro de page, à partir de 1."),
            OpenApiParameter(
                "page_size",
                int,
                description="Nombre de résultats par page, plafonné à 100.",
            ),
            OpenApiParameter(
                "search", str, description="Recherche partielle dans nom, prénom et e-mail."
            ),
            OpenApiParameter(
                "role",
                str,
                enum=["admin", "vendeur"],
                description="Filtre par rôle.",
            ),
            OpenApiParameter(
                "active",
                str,
                enum=["true", "false"],
                description="Filtre par état actif.",
            ),
            OpenApiParameter(
                "ordering",
                str,
                description=(
                    "Tri par nom, prenom, email, role ou date_creation; préfixe - inversant."
                ),
            ),
        ],
        responses={
            200: OpenApiResponse(
                ReponseListeUtilisateursSerializer,
                description="Liste paginée filtrée et triée.",
                examples=exemples_openapi_liste_utilisateurs(
                    "liste_succes",
                    "liste_vide",
                ),
            ),
            400: OpenApiResponse(
                ErreurValidationSerializer,
                description="Filtre ou tri invalide.",
                examples=exemples_openapi_liste_utilisateurs(
                    "liste_filtre_invalide",
                    "liste_tri_invalide",
                ),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description="Jeton d’accès absent, invalide ou expiré.",
                examples=exemples_openapi_liste_utilisateurs(
                    "liste_non_authentifie",
                    "liste_jeton_invalide",
                    "liste_jeton_expire",
                ),
            ),
            403: OpenApiResponse(
                ErreurSerializer,
                description="Rôle insuffisant ou changement de mot de passe requis.",
                examples=exemples_openapi_liste_utilisateurs(
                    "liste_acces_interdit",
                    "liste_changement_mot_de_passe_requis",
                ),
            ),
            404: OpenApiResponse(
                ErreurSerializer,
                description="Numéro de page invalide ou inexistant.",
                examples=exemples_openapi_liste_utilisateurs("liste_page_introuvable"),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_liste_utilisateurs("liste_methode_interdite"),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite de débit atteinte; Retry-After est exprimé en secondes.",
                examples=exemples_openapi_liste_utilisateurs("liste_limite_atteinte"),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_liste_utilisateurs("liste_erreur_interne"),
            ),
        },
    )
    def get(self, requete):
        """Retourne la liste filtrée, triée et paginée des comptes."""
        filtres = FiltresListeUtilisateursSerializer(data=requete.query_params)
        filtres.is_valid(raise_exception=True)
        donnees = filtres.validated_data

        utilisateurs = Utilisateur.objects.all()
        if "role" in donnees:
            utilisateurs = utilisateurs.filter(role=donnees["role"])
        if "active" in donnees:
            utilisateurs = utilisateurs.filter(is_active=donnees["active"] == "true")
        if donnees.get("search"):
            terme = donnees["search"]
            utilisateurs = utilisateurs.filter(
                Q(nom__icontains=terme) | Q(prenom__icontains=terme) | Q(email__icontains=terme)
            )

        ordre = donnees.get("ordering", ["nom"])
        utilisateurs = utilisateurs.order_by(
            *ordre,
            "id",
        )

        pagination = PaginationStandard()
        page = pagination.paginate_queryset(utilisateurs, requete, view=self)
        journaliser_evenement(
            requete._request,
            TypeEvenementSecurite.LISTE_UTILISATEURS_CONSULTEE,
            utilisateur=requete.user,
            details={"nombre_resultats": str(len(page))},
            obligatoire=True,
        )
        return pagination.get_paginated_response(UtilisateurAdminSerializer(page, many=True).data)

    @extend_schema(
        tags=["Utilisateurs"],
        summary="Créer un utilisateur",
        description=(
            "Réservé aux administrateurs. Le nouveau compte reçoit un mot de passe "
            "temporaire haché et doit le changer à sa première connexion. Le mot de "
            "passe n’est jamais renvoyé ni journalisé."
        ),
        operation_id="creer_utilisateur",
        request=UtilisateurCreationSerializer,
        examples=[exemple_requete_openapi_creation_utilisateur()],
        responses={
            201: OpenApiResponse(
                UtilisateurAdminSerializer,
                description="Compte créé; aucun mot de passe n’est retourné.",
                examples=exemples_openapi_creation_utilisateur("creation_succes"),
            ),
            400: OpenApiResponse(
                ErreurValidationSerializer,
                description="Entrée invalide, mot de passe faible ou champ inconnu.",
                examples=exemples_openapi_creation_utilisateur(
                    "creation_email_invalide",
                    "creation_mot_de_passe_faible",
                    "creation_role_invalide",
                    "creation_champs_inconnus",
                    "creation_json_malforme",
                ),
            ),
            401: OpenApiResponse(
                ErreurSerializer,
                description="Jeton d’accès absent, invalide ou expiré.",
                examples=exemples_openapi_creation_utilisateur(
                    "creation_non_authentifie",
                    "creation_jeton_invalide",
                    "creation_jeton_expire",
                ),
            ),
            403: OpenApiResponse(
                ErreurSerializer,
                description="Rôle insuffisant ou changement de mot de passe requis.",
                examples=exemples_openapi_creation_utilisateur(
                    "creation_acces_interdit",
                    "creation_changement_mot_de_passe_requis",
                ),
            ),
            405: OpenApiResponse(
                ErreurSerializer,
                description="Méthode non autorisée.",
                examples=exemples_openapi_creation_utilisateur("creation_methode_interdite"),
            ),
            409: OpenApiResponse(
                ErreurSerializer,
                description="L’adresse e-mail est devenue indisponible pendant la création.",
                examples=exemples_openapi_creation_utilisateur(
                    "creation_email_deja_utilise",
                ),
            ),
            415: OpenApiResponse(
                ErreurValidationSerializer,
                description="Type de contenu non pris en charge.",
                examples=exemples_openapi_creation_utilisateur("creation_type_contenu"),
            ),
            429: OpenApiResponse(
                ErreurSerializer,
                description="Limite de débit atteinte; Retry-After est exprimé en secondes.",
                examples=exemples_openapi_creation_utilisateur("creation_limite_atteinte"),
            ),
            500: OpenApiResponse(
                ErreurSerializer,
                description="Erreur interne sans détail technique.",
                examples=exemples_openapi_creation_utilisateur("creation_erreur_interne"),
            ),
        },
    )
    def post(self, requete):
        """Valide puis crée le compte dans une transaction atomique."""
        serializer = UtilisateurCreationSerializer(data=requete.data)
        serializer.is_valid(raise_exception=True)
        utilisateur = creer_utilisateur_par_administrateur(
            serializer.validated_data,
            requete.user,
            requete._request,
        )
        return Response(
            UtilisateurAdminSerializer(utilisateur).data,
            status=status.HTTP_201_CREATED,
        )

    def get_authenticate_header(self, requete):
        """Fournit un challenge Bearer pour les réponses 401."""
        return "Bearer"

    def handle_exception(self, exception):
        """Journalise les refus sans enregistrer le corps ni le mot de passe."""
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
