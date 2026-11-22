"""Génère la référence JSON depuis les serializers et les exemples canoniques."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.exemples_json import (
    _CODES_HTTP_EXEMPLES,
    _CONDITIONS_EXEMPLES,
    _ENTETES_EXEMPLES,
    EXEMPLE_REQUETE_CHANGEMENT_MOT_DE_PASSE,
    EXEMPLE_REQUETE_CONFIRMATION_REINITIALISATION,
    EXEMPLE_REQUETE_CONNEXION,
    EXEMPLE_REQUETE_CREATION_UTILISATEUR,
    EXEMPLE_REQUETE_DECONNEXION,
    EXEMPLE_REQUETE_MODIFICATION_PROFIL,
    EXEMPLE_REQUETE_MODIFICATION_UTILISATEUR,
    EXEMPLE_REQUETE_RAFRAICHISSEMENT,
    EXEMPLES_JSON_CHANGEMENT_MOT_DE_PASSE,
    EXEMPLES_JSON_CONFIRMATION_REINITIALISATION,
    EXEMPLES_JSON_CONNEXION,
    EXEMPLES_JSON_CREATION_UTILISATEUR,
    EXEMPLES_JSON_DECONNEXION,
    EXEMPLES_JSON_DEMANDE_REINITIALISATION,
    EXEMPLES_JSON_DESACTIVATION_UTILISATEUR,
    EXEMPLES_JSON_DETAIL_UTILISATEUR,
    EXEMPLES_JSON_LISTE_UTILISATEURS,
    EXEMPLES_JSON_MODIFICATION_PROFIL,
    EXEMPLES_JSON_MODIFICATION_UTILISATEUR,
    EXEMPLES_JSON_PROFIL,
    EXEMPLES_JSON_RAFRAICHISSEMENT,
)
from apps.accounts.serializers.connexion import (
    ConnexionSerializer,
    ErreurOuValidationSerializer,
    ErreurSerializer,
    ErreurValidationSerializer,
    ReponseConnexionSerializer,
    UtilisateurResumeConnexionSerializer,
)
from apps.accounts.serializers.jetons import (
    DeconnexionSerializer,
    RafraichissementSerializer,
    ReponseRafraichissementSerializer,
)
from apps.accounts.serializers.mot_de_passe import (
    ChangementMotDePasseSerializer,
    ConfirmationReinitialisationSerializer,
    DemandeReinitialisationSerializer,
)
from apps.accounts.serializers.profil import ProfilModificationSerializer, ProfilSerializer
from apps.accounts.serializers.utilisateurs import (
    FiltresListeUtilisateursSerializer,
    ReponseListeUtilisateursSerializer,
    UtilisateurAdminSerializer,
    UtilisateurCreationSerializer,
    UtilisateurModificationSerializer,
)

_FICHIER_REFERENCE = Path(settings.BASE_DIR) / "docs" / "api" / "REFERENCE_JSON_UTILISATEURS.md"


class Command(BaseCommand):
    """Crée ou vérifie la référence des réponses JSON implémentées."""

    help = "Génère la référence JSON des endpoints utilisateur implémentés."

    def add_arguments(self, parser):
        parser.add_argument(
            "--verifier",
            action="store_true",
            help="Échoue si la référence générée ne correspond pas au fichier commité.",
        )

    def handle(self, *args, **options):
        """Écrit la référence ou confirme qu’elle est à jour."""
        reference = construire_reference_json()
        if options["verifier"]:
            if not _FICHIER_REFERENCE.is_file():
                raise CommandError(f"Référence JSON absente : {_FICHIER_REFERENCE}")
            if _FICHIER_REFERENCE.read_text(encoding="utf-8") != reference:
                raise CommandError("REFERENCE_JSON_UTILISATEURS.md n’est pas à jour.")
            self.stdout.write(self.style.SUCCESS("Référence JSON à jour."))
            return

        _FICHIER_REFERENCE.parent.mkdir(parents=True, exist_ok=True)
        _FICHIER_REFERENCE.write_text(reference, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Référence JSON générée : {_FICHIER_REFERENCE}"))


def construire_reference_json() -> str:
    """Rend la documentation des endpoints implémentés depuis les sources canoniques."""
    morceaux = [
        "# Référence JSON — API Utilisateurs",
        "",
        "> Cette référence couvre les endpoints implémentés. Elle est générée depuis "
        "les serializers et le catalogue d’exemples.",
    ]

    endpoints = (
        (
            "POST `/api/v1/auth/login/`",
            "public. Limitation par IP et e-mail normalisé, même si le compte n’existe pas.",
            EXEMPLE_REQUETE_CONNEXION,
            EXEMPLES_JSON_CONNEXION,
            (
                ("Entrée de connexion", ConnexionSerializer),
                ("Réponse de connexion", ReponseConnexionSerializer),
                ("Résumé utilisateur", UtilisateurResumeConnexionSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "POST `/api/v1/auth/token/refresh/`",
            "public avec un refresh valide. Limitation par adresse IP. L’ancien jeton "
            "est révoqué lors de la rotation; aucun événement n’est journalisé en cas de succès.",
            EXEMPLE_REQUETE_RAFRAICHISSEMENT,
            EXEMPLES_JSON_RAFRAICHISSEMENT,
            (
                ("Entrée de renouvellement", RafraichissementSerializer),
                ("Réponse de renouvellement", ReponseRafraichissementSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "GET `/api/v1/auth/me/`",
            "connecté avec un jeton Bearer d’accès valide; autorisé même si le compte "
            "doit changer son mot de passe.",
            None,
            EXEMPLES_JSON_PROFIL,
            (
                ("Profil", ProfilSerializer),
                ("Erreur", ErreurSerializer),
            ),
        ),
        (
            "POST `/api/v1/auth/logout/`",
            "connecté avec un jeton d’accès valide. Le refresh doit appartenir au même "
            "compte; la révocation est idempotente et limitée par adresse IP.",
            EXEMPLE_REQUETE_DECONNEXION,
            EXEMPLES_JSON_DECONNEXION,
            (
                ("Entrée de déconnexion", DeconnexionSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "POST `/api/v1/users/`",
            "administrateur authentifié dont le mot de passe n’est pas à changer. "
            "Le nouveau compte devra changer son mot de passe à la première connexion.",
            EXEMPLE_REQUETE_CREATION_UTILISATEUR,
            EXEMPLES_JSON_CREATION_UTILISATEUR,
            (
                ("Entrée de création", UtilisateurCreationSerializer),
                ("Utilisateur administrateur", UtilisateurAdminSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "GET `/api/v1/users/`",
            "administrateur authentifié dont le mot de passe n’est pas à changer. "
            "Recherche, filtres, tri autorisé et pagination de 1 à 100 résultats.",
            None,
            EXEMPLES_JSON_LISTE_UTILISATEURS,
            (
                ("Filtres de liste", FiltresListeUtilisateursSerializer),
                ("Réponse paginée", ReponseListeUtilisateursSerializer),
                ("Utilisateur administrateur", UtilisateurAdminSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "GET `/api/v1/users/{uuid}/`",
            "administrateur authentifié dont le mot de passe n’est pas à changer. "
            "L’UUID mal formé ou inconnu retourne la même erreur 404.",
            None,
            EXEMPLES_JSON_DETAIL_UTILISATEUR,
            (
                ("Utilisateur administrateur", UtilisateurAdminSerializer),
                ("Erreur", ErreurSerializer),
            ),
        ),
        (
            "PATCH `/api/v1/users/{uuid}/`",
            "administrateur authentifié dont le mot de passe n’est pas à changer. "
            "Seuls email, nom, prenom, telephone et role sont acceptés; PUT est interdit.",
            EXEMPLE_REQUETE_MODIFICATION_UTILISATEUR,
            EXEMPLES_JSON_MODIFICATION_UTILISATEUR,
            (
                ("Entrée de modification", UtilisateurModificationSerializer),
                ("Utilisateur administrateur", UtilisateurAdminSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "POST `/api/v1/users/{uuid}/deactivate/`",
            "administrateur authentifié dont le mot de passe n’est pas à changer. "
            "Aucun corps n’est accepté; le compte est conservé et ses jetons révoqués.",
            None,
            EXEMPLES_JSON_DESACTIVATION_UTILISATEUR,
            (
                ("Utilisateur administrateur", UtilisateurAdminSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "POST `/api/v1/auth/password/change/`",
            "utilisateur authentifié, même si un changement de mot de passe est exigé. "
            "Le nouveau secret doit respecter les validateurs Django; tous les refresh "
            "sont révoqués après succès.",
            EXEMPLE_REQUETE_CHANGEMENT_MOT_DE_PASSE,
            EXEMPLES_JSON_CHANGEMENT_MOT_DE_PASSE,
            (
                ("Entrée de changement de mot de passe", ChangementMotDePasseSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur métier ou de validation", ErreurOuValidationSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "POST `/api/v1/auth/password/reset/request/`",
            "public, avec limitation par IP et e-mail. La réponse ne révèle pas "
            "l’existence du compte; seul un compte actif reçoit un e-mail.",
            {"email": "rakoto@exemple.com"},
            EXEMPLES_JSON_DEMANDE_REINITIALISATION,
            (
                ("Entrée de demande de réinitialisation", DemandeReinitialisationSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "POST `/api/v1/auth/password/reset/confirm/`",
            "public, avec limitation par IP. UID inconnu, jeton invalide ou expiré "
            "et compte inactif produisent la même réponse.",
            EXEMPLE_REQUETE_CONFIRMATION_REINITIALISATION,
            EXEMPLES_JSON_CONFIRMATION_REINITIALISATION,
            (
                (
                    "Entrée de confirmation de réinitialisation",
                    ConfirmationReinitialisationSerializer,
                ),
                ("Erreur", ErreurSerializer),
                ("Erreur métier ou de validation", ErreurOuValidationSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
        (
            "PATCH `/api/v1/auth/me/`",
            "utilisateur authentifié dont le mot de passe obligatoire a déjà été changé. "
            "Seuls nom, prenom et telephone sont modifiables.",
            EXEMPLE_REQUETE_MODIFICATION_PROFIL,
            EXEMPLES_JSON_MODIFICATION_PROFIL,
            (
                ("Entrée de modification du profil", ProfilModificationSerializer),
                ("Profil", ProfilSerializer),
                ("Erreur", ErreurSerializer),
                ("Erreur de validation", ErreurValidationSerializer),
            ),
        ),
    )

    for route, acces, exemple_requete, exemples, serializers in endpoints:
        morceaux.extend(
            [
                "",
                f"## {route}",
                "",
                f"**Accès :** {acces}",
                "",
            ]
        )
        if exemple_requete is not None:
            morceaux.extend(
                [
                    "### Entrée",
                    "",
                    "```json",
                    json.dumps(exemple_requete, ensure_ascii=False, indent=2),
                    "```",
                    "",
                ]
            )
        morceaux.extend(["### Sorties", "", "| HTTP | Condition | En-têtes |", "|---:|---|---|"])

        for nom in exemples:
            morceaux.append(
                f"| {_CODES_HTTP_EXEMPLES[nom]} | {_CONDITIONS_EXEMPLES[nom]} | "
                f"{_ENTETES_EXEMPLES[nom]} |"
            )
        for nom, exemple in exemples.items():
            corps_json = (
                "Aucun corps JSON."
                if exemple is None
                else f"```json\n{json.dumps(exemple, ensure_ascii=False, indent=2)}\n```"
            )
            morceaux.extend(
                [
                    "",
                    f"#### HTTP {_CODES_HTTP_EXEMPLES[nom]} — {_CONDITIONS_EXEMPLES[nom]}",
                    "",
                    corps_json,
                    "",
                ]
            )

        morceaux.extend(["### Dictionnaire des champs", ""])
        for nom, classe_serializer in serializers:
            morceaux.extend(
                [
                    f"#### {nom}",
                    "",
                    "| Champ | Type | Obligatoire | Signification |",
                    "|---|---|---:|---|",
                ]
            )
            for nom_champ, champ in classe_serializer().fields.items():
                description = str(champ.help_text or "").replace("|", "\\|")
                type_champ = type(champ).__name__.removesuffix("Field")
                morceaux.append(
                    f"| `{nom_champ}` | {type_champ} | "
                    f"{'oui' if champ.required else 'non'} | {description} |"
                )
            morceaux.append("")

    morceaux.extend(
        [
            "## Parcours client",
            "",
            "1. Envoyer les identifiants à `/api/v1/auth/login/` et stocker la paire "
            "JWT reçue de manière sécurisée.",
            "2. Utiliser le jeton `access` pour les requêtes protégées.",
            "3. En cas d’expiration de l’accès, appeler `/api/v1/auth/token/refresh/` "
            "avec le `refresh` courant, remplacer les deux jetons par ceux reçus et "
            "ne jamais réutiliser l’ancien refresh.",
            "4. Pour fermer la session, appeler `/api/v1/auth/logout/` avec le jeton "
            "d’accès et son refresh; la réponse réussie est `204` sans corps.",
            "5. Un administrateur peut créer un compte avec `POST /api/v1/users/`; "
            "le nouveau titulaire doit changer le mot de passe temporaire.",
            "6. Un administrateur peut lister les comptes avec `GET /api/v1/users/`, "
            "en utilisant `search`, `role`, `active`, `ordering`, `page` et `page_size`.",
            "7. Si le renouvellement échoue, demander une nouvelle connexion.",
            "",
        ]
    )

    return "\n".join(morceaux).rstrip() + "\n"
