"""Catalogue JSON canonique réutilisé par Swagger et les tests."""

from typing import Any

from drf_spectacular.utils import OpenApiExample

EXEMPLE_REQUETE_CONNEXION = {
    "email": "rakoto@exemple.com",
    "mot_de_passe": "MotDePasseFort!2026",
}
EXEMPLE_REQUETE_RAFRAICHISSEMENT = {
    "refresh": "<jeton_rafraichissement_exemple>",
}
EXEMPLE_REQUETE_DECONNEXION = {
    "refresh": "<jeton_rafraichissement_exemple>",
}
EXEMPLE_REQUETE_CREATION_UTILISATEUR = {
    "email": "rakoto@exemple.com",
    "nom": "Rakoto",
    "prenom": "Hery",
    "telephone": "+261320000000",
    "role": "vendeur",
    "mot_de_passe_initial": "MotDePasseFort!2026",
}
EXEMPLE_REQUETE_MODIFICATION_UTILISATEUR = {
    "email": "rakoto@exemple.com",
    "nom": "Rakoto",
    "prenom": "Hery",
    "telephone": "+261320000000",
    "role": "vendeur",
}

EXEMPLES_JSON_CONNEXION: dict[str, dict[str, Any]] = {
    "succes": {
        "access": "<jeton_acces_exemple>",
        "refresh": "<jeton_rafraichissement_exemple>",
        "utilisateur": {
            "uuid": "3f1c2b7e-8a4d-4c1e-9b6a-2d5f7e8a9c10",
            "email": "rakoto@exemple.com",
            "nom": "Rakoto",
            "prenom": "Hery",
            "role": "vendeur",
            "doit_changer_mot_de_passe": False,
        },
    },
    "validation": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"email": ["Saisissez une adresse e-mail valide."]},
    },
    "champs_inconnus": {
        "detail": "Les données envoyées sont invalides.",
        "code": "champs_inconnus",
        "erreurs": {"champs_inconnus": ["Champs non autorisés : role"]},
    },
    "json_malforme": {
        "detail": "Le corps JSON est invalide.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "identifiants_invalides": {
        "detail": "E-mail ou mot de passe incorrect.",
        "code": "identifiants_invalides",
    },
    "methode_non_autorisee": {
        "detail": "Méthode non autorisée.",
        "code": "methode_non_autorisee",
    },
    "type_contenu_non_pris_en_charge": {
        "detail": "Le type de contenu n’est pas pris en charge.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "trop_de_requetes": {
        "detail": "Trop de requêtes. Réessayez après le délai indiqué.",
        "code": "trop_de_requetes",
    },
    "erreur_interne": {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    },
}
EXEMPLES_JSON_RAFRAICHISSEMENT: dict[str, dict[str, Any]] = {
    "rafraichissement_succes": {
        "access": "<nouveau_jeton_acces_exemple>",
        "refresh": "<nouveau_jeton_rafraichissement_exemple>",
    },
    "rafraichissement_validation": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"refresh": ["Ce champ est obligatoire."]},
    },
    "rafraichissement_champs_inconnus": {
        "detail": "Les données envoyées sont invalides.",
        "code": "champs_inconnus",
        "erreurs": {"champs_inconnus": ["Champs non autorisés : role"]},
    },
    "rafraichissement_json_malforme": {
        "detail": "Le corps JSON est invalide.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "rafraichissement_jeton_invalide": {
        "detail": "Le jeton de rafraîchissement est invalide.",
        "code": "jeton_invalide",
    },
    "rafraichissement_jeton_expire": {
        "detail": "Le jeton de rafraîchissement a expiré.",
        "code": "jeton_expire",
    },
    "rafraichissement_methode_interdite": {
        "detail": "Méthode non autorisée.",
        "code": "methode_non_autorisee",
    },
    "rafraichissement_type_contenu": {
        "detail": "Le type de contenu n’est pas pris en charge.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "rafraichissement_limite_atteinte": {
        "detail": "Trop de requêtes. Réessayez après le délai indiqué.",
        "code": "trop_de_requetes",
    },
    "rafraichissement_erreur_interne": {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    },
}
EXEMPLES_JSON_PROFIL: dict[str, dict[str, Any]] = {
    "profil_succes": {
        "uuid": "3f1c2b7e-8a4d-4c1e-9b6a-2d5f7e8a9c10",
        "email": "rakoto@exemple.com",
        "nom": "Rakoto",
        "prenom": "Hery",
        "telephone": "+261320000000",
        "role": "vendeur",
        "doit_changer_mot_de_passe": False,
        "date_creation": "2026-11-22T09:30:00+03:00",
        "derniere_connexion": "2026-11-22T10:05:12+03:00",
    },
    "profil_sans_connexion": {
        "uuid": "3f1c2b7e-8a4d-4c1e-9b6a-2d5f7e8a9c10",
        "email": "rakoto@exemple.com",
        "nom": "Rakoto",
        "prenom": "Hery",
        "telephone": "",
        "role": "vendeur",
        "doit_changer_mot_de_passe": False,
        "date_creation": "2026-11-22T09:30:00+03:00",
        "derniere_connexion": None,
    },
    "profil_non_authentifie": {
        "detail": "Authentification requise.",
        "code": "non_authentifie",
    },
    "profil_jeton_expire": {
        "detail": "Le jeton d’accès a expiré.",
        "code": "jeton_expire",
    },
    "profil_jeton_invalide": {
        "detail": "Le jeton d’accès est invalide.",
        "code": "jeton_invalide",
    },
    "profil_methode_interdite": {
        "detail": "Méthode non autorisée.",
        "code": "methode_non_autorisee",
    },
}
EXEMPLES_JSON_DECONNEXION: dict[str, dict[str, Any] | None] = {
    "deconnexion_succes": None,
    "deconnexion_validation": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"refresh": ["Ce champ est obligatoire."]},
    },
    "deconnexion_champs_inconnus": {
        "detail": "Les données envoyées sont invalides.",
        "code": "champs_inconnus",
        "erreurs": {"champs_inconnus": ["Champs non autorisés : role"]},
    },
    "deconnexion_json_malforme": {
        "detail": "Le corps JSON est invalide.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "deconnexion_jeton_invalide": {
        "detail": "Le jeton de rafraîchissement est invalide.",
        "code": "jeton_invalide",
    },
    "deconnexion_non_authentifie": {
        "detail": "Authentification requise.",
        "code": "non_authentifie",
    },
    "deconnexion_acces_invalide": {
        "detail": "Le jeton d’accès est invalide.",
        "code": "jeton_invalide",
    },
    "deconnexion_acces_expire": {
        "detail": "Le jeton d’accès a expiré.",
        "code": "jeton_expire",
    },
    "deconnexion_jeton_non_autorise": {
        "detail": "Accès interdit.",
        "code": "jeton_non_autorise",
    },
    "deconnexion_methode_interdite": {
        "detail": "Méthode non autorisée.",
        "code": "methode_non_autorisee",
    },
    "deconnexion_type_contenu": {
        "detail": "Le type de contenu n’est pas pris en charge.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "deconnexion_limite_atteinte": {
        "detail": "Trop de requêtes. Réessayez après le délai indiqué.",
        "code": "trop_de_requetes",
    },
    "deconnexion_erreur_interne": {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    },
}
EXEMPLES_JSON_CREATION_UTILISATEUR: dict[str, dict[str, Any]] = {
    "creation_succes": {
        "uuid": "3f1c2b7e-8a4d-4c1e-9b6a-2d5f7e8a9c10",
        "email": "rakoto@exemple.com",
        "nom": "Rakoto",
        "prenom": "Hery",
        "telephone": "+261320000000",
        "role": "vendeur",
        "est_actif": True,
        "doit_changer_mot_de_passe": True,
        "date_creation": "2026-11-22T09:30:00+03:00",
        "derniere_connexion": None,
        "date_dernier_changement_mot_de_passe": None,
        "date_modification": "2026-11-22T09:30:00+03:00",
    },
    "creation_email_invalide": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"email": ["Saisissez une adresse e-mail valide."]},
    },
    "creation_mot_de_passe_faible": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {
            "mot_de_passe_initial": [
                "Ce mot de passe est trop court. Il doit contenir au minimum 12 caractères."
            ]
        },
    },
    "creation_role_invalide": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"role": ["Rôle invalide. Choisissez admin ou vendeur."]},
    },
    "creation_champs_inconnus": {
        "detail": "Les données envoyées sont invalides.",
        "code": "champs_inconnus",
        "erreurs": {"champs_inconnus": ["Champs non autorisés : is_superuser"]},
    },
    "creation_json_malforme": {
        "detail": "Le corps JSON est invalide.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "creation_non_authentifie": {
        "detail": "Authentification requise.",
        "code": "non_authentifie",
    },
    "creation_jeton_invalide": {
        "detail": "Le jeton d’accès est invalide.",
        "code": "jeton_invalide",
    },
    "creation_jeton_expire": {
        "detail": "Le jeton d’accès a expiré.",
        "code": "jeton_expire",
    },
    "creation_acces_interdit": {
        "detail": "Accès interdit.",
        "code": "acces_interdit",
    },
    "creation_changement_mot_de_passe_requis": {
        "detail": "Un changement de mot de passe est requis.",
        "code": "changement_mot_de_passe_requis",
    },
    "creation_methode_interdite": {
        "detail": "Méthode non autorisée.",
        "code": "methode_non_autorisee",
    },
    "creation_email_deja_utilise": {
        "detail": "Cette adresse e-mail est déjà utilisée.",
        "code": "email_deja_utilise",
    },
    "creation_type_contenu": {
        "detail": "Le type de contenu n’est pas pris en charge.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "creation_limite_atteinte": {
        "detail": "Trop de requêtes. Réessayez après le délai indiqué.",
        "code": "trop_de_requetes",
    },
    "creation_erreur_interne": {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    },
}
EXEMPLES_JSON_LISTE_UTILISATEURS: dict[str, dict[str, Any]] = {
    "liste_succes": {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "uuid": "3f1c2b7e-8a4d-4c1e-9b6a-2d5f7e8a9c10",
                "email": "rakoto@exemple.com",
                "nom": "Rakoto",
                "prenom": "Hery",
                "telephone": "+261320000000",
                "role": "vendeur",
                "est_actif": True,
                "doit_changer_mot_de_passe": False,
                "date_creation": "2026-11-22T09:30:00+03:00",
                "derniere_connexion": None,
                "date_dernier_changement_mot_de_passe": None,
                "date_modification": "2026-11-22T09:30:00+03:00",
            }
        ],
    },
    "liste_vide": {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    },
    "liste_filtre_invalide": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"role": ["« superadmin » n'est pas un choix valide."]},
    },
    "liste_tri_invalide": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {
            "ordering": [
                "Tri invalide. Champs autorisés : nom, prenom, email, role, date_creation."
            ]
        },
    },
    "liste_non_authentifie": {
        "detail": "Authentification requise.",
        "code": "non_authentifie",
    },
    "liste_jeton_invalide": {
        "detail": "Le jeton d’accès est invalide.",
        "code": "jeton_invalide",
    },
    "liste_jeton_expire": {
        "detail": "Le jeton d’accès a expiré.",
        "code": "jeton_expire",
    },
    "liste_acces_interdit": {
        "detail": "Accès interdit.",
        "code": "acces_interdit",
    },
    "liste_changement_mot_de_passe_requis": {
        "detail": "Un changement de mot de passe est requis.",
        "code": "changement_mot_de_passe_requis",
    },
    "liste_page_introuvable": {
        "detail": "Ressource introuvable.",
        "code": "introuvable",
    },
    "liste_methode_interdite": {
        "detail": "Méthode non autorisée.",
        "code": "methode_non_autorisee",
    },
    "liste_limite_atteinte": {
        "detail": "Trop de requêtes. Réessayez après le délai indiqué.",
        "code": "trop_de_requetes",
    },
    "liste_erreur_interne": {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    },
}
EXEMPLES_JSON_DETAIL_UTILISATEUR: dict[str, dict[str, Any]] = {
    "detail_succes": {
        "uuid": "3f1c2b7e-8a4d-4c1e-9b6a-2d5f7e8a9c10",
        "email": "rakoto@exemple.com",
        "nom": "Rakoto",
        "prenom": "Hery",
        "telephone": "+261320000000",
        "role": "vendeur",
        "est_actif": True,
        "doit_changer_mot_de_passe": False,
        "date_creation": "2026-11-22T09:30:00+03:00",
        "derniere_connexion": None,
        "date_dernier_changement_mot_de_passe": None,
        "date_modification": "2026-11-22T09:30:00+03:00",
    },
    "detail_non_authentifie": {
        "detail": "Authentification requise.",
        "code": "non_authentifie",
    },
    "detail_jeton_invalide": {
        "detail": "Le jeton d’accès est invalide.",
        "code": "jeton_invalide",
    },
    "detail_jeton_expire": {
        "detail": "Le jeton d’accès a expiré.",
        "code": "jeton_expire",
    },
    "detail_acces_interdit": {
        "detail": "Accès interdit.",
        "code": "acces_interdit",
    },
    "detail_changement_mot_de_passe_requis": {
        "detail": "Un changement de mot de passe est requis.",
        "code": "changement_mot_de_passe_requis",
    },
    "detail_uuid_invalide": {
        "detail": "Ressource introuvable.",
        "code": "introuvable",
    },
    "detail_utilisateur_introuvable": {
        "detail": "Ressource introuvable.",
        "code": "introuvable",
    },
    "detail_methode_interdite": {
        "detail": "Méthode non autorisée.",
        "code": "methode_non_autorisee",
    },
    "detail_limite_atteinte": {
        "detail": "Trop de requêtes. Réessayez après le délai indiqué.",
        "code": "trop_de_requetes",
    },
    "detail_erreur_interne": {
        "detail": "Erreur interne du serveur.",
        "code": "erreur_interne",
    },
}
EXEMPLES_JSON_MODIFICATION_UTILISATEUR: dict[str, dict[str, Any]] = {
    "modification_succes": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_succes"],
    "modification_validation": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"email": ["Saisissez une adresse e-mail valide."]},
    },
    "modification_champs_inconnus": {
        "detail": "Les données envoyées sont invalides.",
        "code": "champs_inconnus",
        "erreurs": {
            "champs_inconnus": ["Champs non autorisés : mot_de_passe"],
        },
    },
    "modification_json_malforme": {
        "detail": "Le corps JSON est invalide.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "modification_type_contenu": {
        "detail": "Le type de contenu n’est pas pris en charge.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "modification_non_authentifie": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_non_authentifie"],
    "modification_jeton_invalide": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_jeton_invalide"],
    "modification_jeton_expire": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_jeton_expire"],
    "modification_acces_interdit": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_acces_interdit"],
    "modification_changement_mot_de_passe_requis": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_changement_mot_de_passe_requis"
    ],
    "modification_role_propre_interdit": {
        "detail": "Un administrateur ne peut pas modifier son propre rôle.",
        "code": "auto_modification_role_interdite",
    },
    "modification_uuid_invalide": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_uuid_invalide"],
    "modification_utilisateur_introuvable": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_utilisateur_introuvable"
    ],
    "modification_methode_interdite": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_methode_interdite"],
    "modification_email_conflit": {
        "detail": "Cette adresse e-mail est déjà utilisée.",
        "code": "email_deja_utilise",
    },
    "modification_dernier_administrateur": {
        "detail": "Le dernier administrateur actif ne peut pas être rétrogradé.",
        "code": "dernier_administrateur",
    },
    "modification_limite_atteinte": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_limite_atteinte"],
    "modification_erreur_interne": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_erreur_interne"],
}
EXEMPLES_JSON_DESACTIVATION_UTILISATEUR: dict[str, dict[str, Any]] = {
    "desactivation_succes": {
        **EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_succes"],
        "est_actif": False,
    },
    "desactivation_corps_interdit": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"corps": ["Cette route n’accepte pas de corps."]},
    },
    "desactivation_non_authentifie": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_non_authentifie"],
    "desactivation_jeton_invalide": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_jeton_invalide"],
    "desactivation_jeton_expire": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_jeton_expire"],
    "desactivation_acces_interdit": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_acces_interdit"],
    "desactivation_changement_mot_de_passe_requis": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_changement_mot_de_passe_requis"
    ],
    "desactivation_auto_interdite": {
        "detail": "Un administrateur ne peut pas se désactiver lui-même.",
        "code": "auto_desactivation_interdite",
    },
    "desactivation_uuid_invalide": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_uuid_invalide"],
    "desactivation_utilisateur_introuvable": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_utilisateur_introuvable"
    ],
    "desactivation_methode_interdite": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_methode_interdite"],
    "desactivation_dernier_administrateur": {
        "detail": "Le dernier administrateur actif ne peut pas être désactivé.",
        "code": "dernier_administrateur",
    },
    "desactivation_deja_inactif": {
        "detail": "Ce compte est déjà désactivé.",
        "code": "compte_deja_desactive",
    },
    "desactivation_limite_atteinte": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_limite_atteinte"],
    "desactivation_erreur_interne": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_erreur_interne"],
}
EXEMPLE_REQUETE_CHANGEMENT_MOT_DE_PASSE = {
    "ancien_mot_de_passe": "AncienMotDePasse!2026",
    "nouveau_mot_de_passe": "NouveauMotDePasse!2026",
    "confirmation_nouveau_mot_de_passe": "NouveauMotDePasse!2026",
}
EXEMPLES_JSON_CHANGEMENT_MOT_DE_PASSE: dict[str, dict[str, Any]] = {
    "changement_succes": {
        "detail": "Mot de passe modifié. Veuillez vous reconnecter.",
    },
    "changement_ancien_incorrect": {
        "detail": "L’ancien mot de passe est incorrect.",
        "code": "ancien_mot_de_passe_incorrect",
    },
    "changement_validation": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {
            "nouveau_mot_de_passe": [
                "Ce mot de passe est trop court. Il doit contenir au minimum 12 caractères."
            ]
        },
    },
    "changement_confirmation_invalide": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {
            "confirmation_nouveau_mot_de_passe": [
                "La confirmation du mot de passe ne correspond pas."
            ]
        },
    },
    "changement_mot_de_passe_identique": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {
            "nouveau_mot_de_passe": ["Le nouveau mot de passe doit être différent de l’ancien."]
        },
    },
    "changement_champs_inconnus": {
        "detail": "Les données envoyées sont invalides.",
        "code": "champs_inconnus",
        "erreurs": {"champs_inconnus": ["Champs non autorisés : role"]},
    },
    "changement_json_malforme": {
        "detail": "Le corps JSON est invalide.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "changement_non_authentifie": EXEMPLES_JSON_PROFIL["profil_non_authentifie"],
    "changement_jeton_invalide": EXEMPLES_JSON_PROFIL["profil_jeton_invalide"],
    "changement_jeton_expire": EXEMPLES_JSON_PROFIL["profil_jeton_expire"],
    "changement_methode_interdite": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_methode_interdite"],
    "changement_type_contenu": EXEMPLES_JSON_CREATION_UTILISATEUR["creation_type_contenu"],
    "changement_limite_atteinte": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_limite_atteinte"],
    "changement_erreur_interne": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_erreur_interne"],
}
EXEMPLES_JSON_DEMANDE_REINITIALISATION: dict[str, dict[str, Any]] = {
    "demande_reinitialisation_succes": {
        "detail": (
            "Si un compte correspond à cette adresse, un e-mail de réinitialisation a été envoyé."
        ),
    },
    "demande_reinitialisation_email_invalide": EXEMPLES_JSON_CREATION_UTILISATEUR[
        "creation_email_invalide"
    ],
    "demande_reinitialisation_champs_inconnus": {
        "detail": "Les données envoyées sont invalides.",
        "code": "champs_inconnus",
        "erreurs": {"champs_inconnus": ["Champs non autorisés : role"]},
    },
    "demande_reinitialisation_json_malforme": EXEMPLES_JSON_CREATION_UTILISATEUR[
        "creation_json_malforme"
    ],
    "demande_reinitialisation_type_contenu": EXEMPLES_JSON_CREATION_UTILISATEUR[
        "creation_type_contenu"
    ],
    "demande_reinitialisation_methode_interdite": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_methode_interdite"
    ],
    "demande_reinitialisation_limite_atteinte": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_limite_atteinte"
    ],
    "demande_reinitialisation_erreur_interne": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_erreur_interne"
    ],
}
_PLACEHOLDER_OPENAPI = "<jeton_reinitialisation_exemple>"
EXEMPLE_REQUETE_CONFIRMATION_REINITIALISATION = {
    "uid": "3f1c2b7e-8a4d-4c1e-9b6a-2d5f7e8a9c10",
    "token": _PLACEHOLDER_OPENAPI,
    "nouveau_mot_de_passe": "NouveauMotDePasse!2026",
    "confirmation_nouveau_mot_de_passe": "NouveauMotDePasse!2026",
}
EXEMPLES_JSON_CONFIRMATION_REINITIALISATION: dict[str, dict[str, Any]] = {
    "confirmation_reinitialisation_succes": {
        "detail": "Mot de passe réinitialisé. Vous pouvez vous connecter.",
    },
    "confirmation_reinitialisation_jeton_invalide": {
        "detail": "Lien de réinitialisation invalide ou expiré.",
        "code": "jeton_invalide",
    },
    "confirmation_reinitialisation_validation": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {
            "nouveau_mot_de_passe": [
                "Ce mot de passe est trop court. Il doit contenir au minimum 12 caractères."
            ]
        },
    },
    "confirmation_reinitialisation_confirmation_invalide": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {
            "confirmation_nouveau_mot_de_passe": [
                "La confirmation du mot de passe ne correspond pas."
            ]
        },
    },
    "confirmation_reinitialisation_champs_inconnus": {
        "detail": "Les données envoyées sont invalides.",
        "code": "champs_inconnus",
        "erreurs": {"champs_inconnus": ["Champs non autorisés : role"]},
    },
    "confirmation_reinitialisation_json_malforme": {
        "detail": "Le corps JSON est invalide.",
        "code": "donnees_invalides",
        "erreurs": {},
    },
    "confirmation_reinitialisation_type_contenu": EXEMPLES_JSON_CREATION_UTILISATEUR[
        "creation_type_contenu"
    ],
    "confirmation_reinitialisation_methode_interdite": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_methode_interdite"
    ],
    "confirmation_reinitialisation_limite_atteinte": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_limite_atteinte"
    ],
    "confirmation_reinitialisation_erreur_interne": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_erreur_interne"
    ],
}
EXEMPLE_REQUETE_MODIFICATION_PROFIL = {
    "nom": "Rakoto",
    "prenom": "Hery",
    "telephone": "+261320000000",
}
EXEMPLES_JSON_MODIFICATION_PROFIL: dict[str, dict[str, Any]] = {
    "profil_modification_succes": EXEMPLES_JSON_PROFIL["profil_succes"],
    "profil_modification_validation": {
        "detail": "Les données envoyées sont invalides.",
        "code": "donnees_invalides",
        "erreurs": {"telephone": ["Saisissez un numéro de téléphone valide."]},
    },
    "profil_modification_champs_inconnus": {
        "detail": "Les données envoyées sont invalides.",
        "code": "champs_inconnus",
        "erreurs": {"champs_inconnus": ["Champs non autorisés : role"]},
    },
    "profil_modification_json_malforme": EXEMPLES_JSON_CREATION_UTILISATEUR[
        "creation_json_malforme"
    ],
    "profil_modification_type_contenu": EXEMPLES_JSON_CREATION_UTILISATEUR["creation_type_contenu"],
    "profil_modification_non_authentifie": EXEMPLES_JSON_PROFIL["profil_non_authentifie"],
    "profil_modification_jeton_invalide": EXEMPLES_JSON_PROFIL["profil_jeton_invalide"],
    "profil_modification_jeton_expire": EXEMPLES_JSON_PROFIL["profil_jeton_expire"],
    "profil_modification_changement_mot_de_passe_requis": (
        EXEMPLES_JSON_CREATION_UTILISATEUR["creation_changement_mot_de_passe_requis"]
    ),
    "profil_modification_methode_interdite": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_methode_interdite"
    ],
    "profil_modification_limite_atteinte": EXEMPLES_JSON_DETAIL_UTILISATEUR[
        "detail_limite_atteinte"
    ],
    "profil_modification_erreur_interne": EXEMPLES_JSON_DETAIL_UTILISATEUR["detail_erreur_interne"],
}

_METADONNEES_EXEMPLES = {
    "succes": ("Connexion réussie", "Paire de jetons et résumé du compte."),
    "validation": ("E-mail invalide", "Erreur de validation des champs."),
    "champs_inconnus": ("Champ inconnu", "Le corps contient un champ non autorisé."),
    "json_malforme": ("JSON malformé", "Le corps ne peut pas être analysé."),
    "identifiants_invalides": (
        "Identifiants incorrects",
        "Même réponse pour un compte inconnu, inactif ou un mot de passe erroné.",
    ),
    "methode_non_autorisee": ("Méthode interdite", "La route accepte uniquement POST."),
    "type_contenu_non_pris_en_charge": (
        "Type de contenu non pris en charge",
        "Le corps doit être transmis en application/json.",
    ),
    "trop_de_requetes": ("Limite atteinte", "La réponse contient le délai Retry-After."),
    "erreur_interne": ("Erreur interne", "Aucun détail technique n’est exposé."),
    "rafraichissement_succes": (
        "Jetons renouvelés",
        "Nouveaux jetons; l’ancien refresh est révoqué.",
    ),
    "rafraichissement_validation": ("Entrée invalide", "Le champ refresh est requis."),
    "rafraichissement_champs_inconnus": (
        "Champ inconnu",
        "Le corps contient une propriété non autorisée.",
    ),
    "rafraichissement_json_malforme": ("JSON malformé", "Le corps ne peut pas être analysé."),
    "rafraichissement_jeton_invalide": (
        "Jeton invalide",
        "Jeton falsifié, révoqué, de mauvais type ou associé à un compte désactivé.",
    ),
    "rafraichissement_jeton_expire": ("Jeton expiré", "Le jeton de rafraîchissement a expiré."),
    "rafraichissement_methode_interdite": (
        "Méthode interdite",
        "La route accepte uniquement POST.",
    ),
    "rafraichissement_type_contenu": (
        "Type de contenu non pris en charge",
        "Le corps doit être transmis en application/json.",
    ),
    "rafraichissement_limite_atteinte": (
        "Limite atteinte",
        "La limite de renouvellements par IP est dépassée.",
    ),
    "rafraichissement_erreur_interne": ("Erreur interne", "Aucun détail technique n’est exposé."),
    "profil_succes": ("Profil du compte", "Profil complet du titulaire du jeton."),
    "profil_sans_connexion": (
        "Profil sans connexion précédente",
        "Le champ derniere_connexion est toujours présent et vaut null.",
    ),
    "profil_non_authentifie": ("Jeton absent", "Aucun jeton d’accès n’a été transmis."),
    "profil_jeton_expire": ("Jeton expiré", "Le jeton d’accès a expiré."),
    "profil_jeton_invalide": (
        "Jeton invalide",
        "Le jeton est falsifié, illisible ou associé à un compte désactivé.",
    ),
    "profil_methode_interdite": (
        "Méthode interdite",
        "Seules les méthodes GET et PATCH sont autorisées.",
    ),
    "deconnexion_succes": (
        "Déconnexion réussie",
        "Aucun corps n’est retourné; le jeton est révoqué.",
    ),
    "deconnexion_validation": ("Entrée invalide", "Le champ refresh est requis."),
    "deconnexion_champs_inconnus": (
        "Champ inconnu",
        "Le corps contient une propriété non autorisée.",
    ),
    "deconnexion_json_malforme": ("JSON malformé", "Le corps ne peut pas être analysé."),
    "deconnexion_jeton_invalide": (
        "Jeton invalide",
        "Le jeton de rafraîchissement est mal formé, expiré ou d’un type incorrect.",
    ),
    "deconnexion_non_authentifie": ("Jeton d’accès absent", "Aucun accès valide n’a été fourni."),
    "deconnexion_acces_invalide": (
        "Jeton d’accès invalide",
        "Le jeton d’accès est falsifié ou associé à un compte désactivé.",
    ),
    "deconnexion_acces_expire": ("Jeton d’accès expiré", "Le jeton d’accès a expiré."),
    "deconnexion_jeton_non_autorise": (
        "Jeton appartenant à un autre compte",
        "Le jeton de rafraîchissement n’est pas révoqué.",
    ),
    "deconnexion_methode_interdite": ("Méthode interdite", "La route accepte uniquement POST."),
    "deconnexion_type_contenu": (
        "Type de contenu non pris en charge",
        "Le corps doit être transmis en application/json.",
    ),
    "deconnexion_limite_atteinte": (
        "Limite atteinte",
        "La limite de déconnexions par IP est dépassée.",
    ),
    "deconnexion_erreur_interne": ("Erreur interne", "Aucun détail technique n’est exposé."),
    "creation_succes": ("Utilisateur créé", "Compte actif sans donnée de mot de passe."),
    "creation_email_invalide": ("E-mail invalide", "L’adresse e-mail est mal formée."),
    "creation_mot_de_passe_faible": (
        "Mot de passe faible",
        "Le mot de passe ne respecte pas la politique de sécurité.",
    ),
    "creation_role_invalide": ("Rôle invalide", "Seuls les rôles admin et vendeur sont admis."),
    "creation_champs_inconnus": (
        "Champ sensible refusé",
        "Les propriétés hors liste blanche sont refusées.",
    ),
    "creation_json_malforme": ("JSON malformé", "Le corps ne peut pas être analysé."),
    "creation_non_authentifie": ("Jeton absent", "Aucun jeton d’accès n’a été transmis."),
    "creation_jeton_invalide": (
        "Jeton invalide",
        "Le jeton d’accès est falsifié ou le compte est inactif.",
    ),
    "creation_jeton_expire": ("Jeton expiré", "Le jeton d’accès a expiré."),
    "creation_acces_interdit": ("Rôle insuffisant", "La création est réservée aux admins."),
    "creation_changement_mot_de_passe_requis": (
        "Changement de mot de passe requis",
        "L’administrateur doit d’abord changer son mot de passe.",
    ),
    "creation_methode_interdite": ("Méthode interdite", "La route accepte uniquement POST."),
    "creation_email_deja_utilise": (
        "Conflit d’e-mail",
        "Une création concurrente a utilisé la même adresse.",
    ),
    "creation_type_contenu": (
        "Type de contenu non pris en charge",
        "Le corps doit être transmis en application/json.",
    ),
    "creation_limite_atteinte": (
        "Limite atteinte",
        "La limite générale par utilisateur est dépassée.",
    ),
    "creation_erreur_interne": ("Erreur interne", "Aucun détail technique n’est exposé."),
    "liste_succes": ("Utilisateurs trouvés", "Réponse paginée avec un résultat complet."),
    "liste_vide": ("Aucun résultat", "Les filtres ne correspondent à aucun compte."),
    "liste_filtre_invalide": ("Filtre invalide", "La valeur du rôle ne fait pas partie des choix."),
    "liste_tri_invalide": (
        "Tri non autorisé",
        "La liste de tri ne contient que les champs explicitement autorisés.",
    ),
    "liste_non_authentifie": ("Jeton absent", "Aucun jeton d’accès n’a été transmis."),
    "liste_jeton_invalide": (
        "Jeton invalide",
        "Le jeton d’accès est falsifié ou le compte est inactif.",
    ),
    "liste_jeton_expire": ("Jeton expiré", "Le jeton d’accès a expiré."),
    "liste_acces_interdit": ("Rôle insuffisant", "La liste est réservée aux admins."),
    "liste_changement_mot_de_passe_requis": (
        "Changement de mot de passe requis",
        "L’administrateur doit d’abord changer son mot de passe.",
    ),
    "liste_page_introuvable": ("Page inconnue", "Le numéro de page est invalide ou inexistant."),
    "liste_methode_interdite": ("Méthode interdite", "La route accepte uniquement GET."),
    "liste_limite_atteinte": (
        "Limite atteinte",
        "La limite générale par utilisateur est dépassée.",
    ),
    "liste_erreur_interne": ("Erreur interne", "Aucun détail technique n’est exposé."),
    "detail_succes": ("Utilisateur trouvé", "Compte complet sans champs sensibles."),
    "detail_non_authentifie": ("Jeton absent", "Aucun jeton d’accès n’a été transmis."),
    "detail_jeton_invalide": (
        "Jeton invalide",
        "Le jeton d’accès est falsifié ou le compte inactif.",
    ),
    "detail_jeton_expire": ("Jeton expiré", "Le jeton d’accès a expiré."),
    "detail_acces_interdit": ("Rôle insuffisant", "La consultation est réservée aux admins."),
    "detail_changement_mot_de_passe_requis": (
        "Changement de mot de passe requis",
        "L’administrateur doit d’abord changer son mot de passe.",
    ),
    "detail_uuid_invalide": ("UUID mal formé", "Le segment UUID est invalide."),
    "detail_utilisateur_introuvable": (
        "Utilisateur inconnu",
        "Aucun compte ne correspond à l’UUID.",
    ),
    "detail_methode_interdite": ("Méthode interdite", "La route accepte uniquement GET."),
    "detail_limite_atteinte": (
        "Limite atteinte",
        "La limite générale par utilisateur est dépassée.",
    ),
    "detail_erreur_interne": ("Erreur interne", "Aucun détail technique n’est exposé."),
    "modification_succes": (
        "Utilisateur modifié",
        "Réponse administrative sans champs sensibles.",
    ),
    "modification_validation": (
        "Donnée invalide",
        "Une valeur de champ ne respecte pas le format.",
    ),
    "modification_champs_inconnus": (
        "Champ interdit",
        "Le corps contient un champ non autorisé.",
    ),
    "modification_json_malforme": ("JSON malformé", "Le corps ne peut pas être analysé."),
    "modification_type_contenu": (
        "Type de contenu non pris en charge",
        "Le corps doit être transmis en application/json.",
    ),
    "modification_non_authentifie": ("Jeton absent", "Aucun jeton d’accès n’a été transmis."),
    "modification_jeton_invalide": (
        "Jeton invalide",
        "Le jeton d’accès est falsifié ou le compte inactif.",
    ),
    "modification_jeton_expire": ("Jeton expiré", "Le jeton d’accès a expiré."),
    "modification_acces_interdit": (
        "Rôle insuffisant",
        "La modification est réservée aux admins.",
    ),
    "modification_changement_mot_de_passe_requis": (
        "Changement de mot de passe requis",
        "L’administrateur doit d’abord changer son mot de passe.",
    ),
    "modification_role_propre_interdit": (
        "Auto-modification interdite",
        "Un administrateur ne peut pas modifier son propre rôle.",
    ),
    "modification_uuid_invalide": ("UUID mal formé", "Le segment UUID est invalide."),
    "modification_utilisateur_introuvable": (
        "Utilisateur inconnu",
        "Aucun compte ne correspond à l’UUID.",
    ),
    "modification_methode_interdite": (
        "Méthode interdite",
        "PUT et autres méthodes sont refusées.",
    ),
    "modification_email_conflit": (
        "Conflit d’e-mail",
        "Une création concurrente a utilisé la même adresse.",
    ),
    "modification_dernier_administrateur": (
        "Dernier administrateur",
        "Le dernier administrateur actif ne peut pas être rétrogradé.",
    ),
    "modification_limite_atteinte": (
        "Limite atteinte",
        "La limite générale par utilisateur est dépassée.",
    ),
    "modification_erreur_interne": ("Erreur interne", "Aucun détail technique n’est exposé."),
    "desactivation_succes": (
        "Compte désactivé",
        "Compte inactif, jetons révoqués et données conservées.",
    ),
    "desactivation_corps_interdit": (
        "Corps interdit",
        "Cette action ne reçoit aucune donnée.",
    ),
    "desactivation_non_authentifie": ("Jeton absent", "Aucun jeton d’accès n’a été transmis."),
    "desactivation_jeton_invalide": (
        "Jeton invalide",
        "Le jeton d’accès est falsifié ou le compte inactif.",
    ),
    "desactivation_jeton_expire": ("Jeton expiré", "Le jeton d’accès a expiré."),
    "desactivation_acces_interdit": (
        "Rôle insuffisant",
        "La désactivation est réservée aux admins.",
    ),
    "desactivation_changement_mot_de_passe_requis": (
        "Changement de mot de passe requis",
        "L’administrateur doit d’abord changer son mot de passe.",
    ),
    "desactivation_auto_interdite": (
        "Auto-désactivation interdite",
        "Un administrateur ne peut pas désactiver son propre compte.",
    ),
    "desactivation_uuid_invalide": ("UUID mal formé", "Le segment UUID est invalide."),
    "desactivation_utilisateur_introuvable": (
        "Utilisateur inconnu",
        "Aucun compte ne correspond à l’UUID.",
    ),
    "desactivation_methode_interdite": (
        "Méthode interdite",
        "La route accepte uniquement POST.",
    ),
    "desactivation_dernier_administrateur": (
        "Dernier administrateur",
        "Le dernier administrateur actif ne peut pas être désactivé.",
    ),
    "desactivation_deja_inactif": (
        "Compte déjà désactivé",
        "Une nouvelle désactivation est refusée.",
    ),
    "desactivation_limite_atteinte": (
        "Limite atteinte",
        "La limite générale par utilisateur est dépassée.",
    ),
    "desactivation_erreur_interne": (
        "Erreur interne",
        "Aucun détail technique n’est exposé.",
    ),
    "changement_succes": ("Mot de passe modifié", "Toutes les sessions précédentes sont fermées."),
    "changement_ancien_incorrect": (
        "Ancien mot de passe incorrect",
        "Le mot de passe actuel ne correspond pas au compte.",
    ),
    "changement_validation": (
        "Mot de passe faible",
        "Le nouveau secret ne respecte pas la politique.",
    ),
    "changement_confirmation_invalide": (
        "Confirmation invalide",
        "La confirmation ne correspond pas au nouveau mot de passe.",
    ),
    "changement_mot_de_passe_identique": (
        "Mot de passe identique",
        "Le nouveau mot de passe doit différer de l’ancien.",
    ),
    "changement_champs_inconnus": (
        "Champ interdit",
        "Seuls les trois champs de mot de passe sont admis.",
    ),
    "changement_json_malforme": ("JSON malformé", "Le corps ne peut pas être analysé."),
    "changement_non_authentifie": ("Jeton absent", "Aucun jeton d’accès n’a été transmis."),
    "changement_jeton_invalide": ("Jeton invalide", "Le jeton d’accès est invalide."),
    "changement_jeton_expire": ("Jeton expiré", "Le jeton d’accès est expiré."),
    "changement_methode_interdite": ("Méthode interdite", "La route accepte uniquement POST."),
    "changement_type_contenu": (
        "Type de contenu non pris en charge",
        "Le corps doit être transmis en application/json.",
    ),
    "changement_limite_atteinte": ("Limite atteinte", "La limite par compte est dépassée."),
    "changement_erreur_interne": ("Erreur interne", "Aucun détail technique n’est exposé."),
    "demande_reinitialisation_succes": (
        "Demande acceptée",
        "La réponse est identique que le compte existe ou non.",
    ),
    "demande_reinitialisation_email_invalide": (
        "E-mail invalide",
        "L’adresse ne respecte pas le format requis.",
    ),
    "demande_reinitialisation_champs_inconnus": (
        "Champ interdit",
        "Seul le champ email est accepté.",
    ),
    "demande_reinitialisation_json_malforme": (
        "JSON malformé",
        "Le corps ne peut pas être analysé.",
    ),
    "demande_reinitialisation_type_contenu": (
        "Type de contenu non pris en charge",
        "Le corps doit être transmis en application/json.",
    ),
    "demande_reinitialisation_methode_interdite": (
        "Méthode interdite",
        "La route accepte uniquement POST.",
    ),
    "demande_reinitialisation_limite_atteinte": (
        "Limite atteinte",
        "La limite par IP ou e-mail est dépassée.",
    ),
    "demande_reinitialisation_erreur_interne": (
        "Erreur interne",
        "Aucun détail technique n’est exposé.",
    ),
    "confirmation_reinitialisation_succes": (
        "Mot de passe réinitialisé",
        "Le lien est consommé et toutes les sessions sont fermées.",
    ),
    "confirmation_reinitialisation_jeton_invalide": (
        "Lien invalide ou expiré",
        "La réponse est identique pour tout lien inutilisable.",
    ),
    "confirmation_reinitialisation_validation": (
        "Mot de passe faible",
        "Le nouveau secret ne respecte pas la politique.",
    ),
    "confirmation_reinitialisation_confirmation_invalide": (
        "Confirmation invalide",
        "La confirmation ne correspond pas au nouveau mot de passe.",
    ),
    "confirmation_reinitialisation_champs_inconnus": (
        "Champ interdit",
        "Seuls les champs de confirmation sont admis.",
    ),
    "confirmation_reinitialisation_json_malforme": (
        "JSON malformé",
        "Le corps ne peut pas être analysé.",
    ),
    "confirmation_reinitialisation_type_contenu": (
        "Type de contenu non pris en charge",
        "Le corps doit être transmis en application/json.",
    ),
    "confirmation_reinitialisation_methode_interdite": (
        "Méthode interdite",
        "La route accepte uniquement POST.",
    ),
    "confirmation_reinitialisation_limite_atteinte": (
        "Limite atteinte",
        "La limite par IP est dépassée.",
    ),
    "confirmation_reinitialisation_erreur_interne": (
        "Erreur interne",
        "Aucun détail technique n’est exposé.",
    ),
    "profil_modification_succes": ("Profil modifié", "Les champs autorisés ont été actualisés."),
    "profil_modification_validation": (
        "Téléphone invalide",
        "Le format du téléphone est invalide.",
    ),
    "profil_modification_champs_inconnus": (
        "Champ interdit",
        "L’e-mail, le rôle et les indicateurs internes ne sont pas modifiables.",
    ),
    "profil_modification_json_malforme": ("JSON malformé", "Le corps ne peut pas être analysé."),
    "profil_modification_type_contenu": (
        "Type de contenu non pris en charge",
        "Le corps doit être transmis en application/json.",
    ),
    "profil_modification_non_authentifie": (
        "Jeton absent",
        "Aucun jeton d’accès n’a été transmis.",
    ),
    "profil_modification_jeton_invalide": ("Jeton invalide", "Le jeton d’accès est invalide."),
    "profil_modification_jeton_expire": ("Jeton expiré", "Le jeton d’accès est expiré."),
    "profil_modification_changement_mot_de_passe_requis": (
        "Changement de mot de passe requis",
        "Le titulaire doit changer son mot de passe avant de modifier son profil.",
    ),
    "profil_modification_methode_interdite": (
        "Méthode interdite",
        "La route accepte uniquement PATCH.",
    ),
    "profil_modification_limite_atteinte": (
        "Limite atteinte",
        "La limite générale par utilisateur est dépassée.",
    ),
    "profil_modification_erreur_interne": (
        "Erreur interne",
        "Aucun détail technique n’est exposé.",
    ),
}
_CODES_HTTP_EXEMPLES = {
    "succes": "200",
    "validation": "400",
    "champs_inconnus": "400",
    "json_malforme": "400",
    "identifiants_invalides": "401",
    "methode_non_autorisee": "405",
    "type_contenu_non_pris_en_charge": "415",
    "trop_de_requetes": "429",
    "erreur_interne": "500",
    "rafraichissement_succes": "200",
    "rafraichissement_validation": "400",
    "rafraichissement_champs_inconnus": "400",
    "rafraichissement_json_malforme": "400",
    "rafraichissement_jeton_invalide": "401",
    "rafraichissement_jeton_expire": "401",
    "rafraichissement_methode_interdite": "405",
    "rafraichissement_type_contenu": "415",
    "rafraichissement_limite_atteinte": "429",
    "rafraichissement_erreur_interne": "500",
    "profil_succes": "200",
    "profil_sans_connexion": "200",
    "profil_non_authentifie": "401",
    "profil_jeton_expire": "401",
    "profil_jeton_invalide": "401",
    "profil_methode_interdite": "405",
    "deconnexion_succes": "204",
    "deconnexion_validation": "400",
    "deconnexion_champs_inconnus": "400",
    "deconnexion_json_malforme": "400",
    "deconnexion_jeton_invalide": "400",
    "deconnexion_non_authentifie": "401",
    "deconnexion_acces_invalide": "401",
    "deconnexion_acces_expire": "401",
    "deconnexion_jeton_non_autorise": "403",
    "deconnexion_methode_interdite": "405",
    "deconnexion_type_contenu": "415",
    "deconnexion_limite_atteinte": "429",
    "deconnexion_erreur_interne": "500",
    "creation_succes": "201",
    "creation_email_invalide": "400",
    "creation_mot_de_passe_faible": "400",
    "creation_role_invalide": "400",
    "creation_champs_inconnus": "400",
    "creation_json_malforme": "400",
    "creation_non_authentifie": "401",
    "creation_jeton_invalide": "401",
    "creation_jeton_expire": "401",
    "creation_acces_interdit": "403",
    "creation_changement_mot_de_passe_requis": "403",
    "creation_methode_interdite": "405",
    "creation_email_deja_utilise": "409",
    "creation_type_contenu": "415",
    "creation_limite_atteinte": "429",
    "creation_erreur_interne": "500",
    "liste_succes": "200",
    "liste_vide": "200",
    "liste_filtre_invalide": "400",
    "liste_tri_invalide": "400",
    "liste_non_authentifie": "401",
    "liste_jeton_invalide": "401",
    "liste_jeton_expire": "401",
    "liste_acces_interdit": "403",
    "liste_changement_mot_de_passe_requis": "403",
    "liste_page_introuvable": "404",
    "liste_methode_interdite": "405",
    "liste_limite_atteinte": "429",
    "liste_erreur_interne": "500",
    "detail_succes": "200",
    "detail_non_authentifie": "401",
    "detail_jeton_invalide": "401",
    "detail_jeton_expire": "401",
    "detail_acces_interdit": "403",
    "detail_changement_mot_de_passe_requis": "403",
    "detail_uuid_invalide": "404",
    "detail_utilisateur_introuvable": "404",
    "detail_methode_interdite": "405",
    "detail_limite_atteinte": "429",
    "detail_erreur_interne": "500",
    "modification_succes": "200",
    "modification_validation": "400",
    "modification_champs_inconnus": "400",
    "modification_json_malforme": "400",
    "modification_type_contenu": "415",
    "modification_non_authentifie": "401",
    "modification_jeton_invalide": "401",
    "modification_jeton_expire": "401",
    "modification_acces_interdit": "403",
    "modification_changement_mot_de_passe_requis": "403",
    "modification_role_propre_interdit": "403",
    "modification_uuid_invalide": "404",
    "modification_utilisateur_introuvable": "404",
    "modification_methode_interdite": "405",
    "modification_email_conflit": "409",
    "modification_dernier_administrateur": "409",
    "modification_limite_atteinte": "429",
    "modification_erreur_interne": "500",
    "desactivation_succes": "200",
    "desactivation_corps_interdit": "400",
    "desactivation_non_authentifie": "401",
    "desactivation_jeton_invalide": "401",
    "desactivation_jeton_expire": "401",
    "desactivation_acces_interdit": "403",
    "desactivation_changement_mot_de_passe_requis": "403",
    "desactivation_auto_interdite": "403",
    "desactivation_uuid_invalide": "404",
    "desactivation_utilisateur_introuvable": "404",
    "desactivation_methode_interdite": "405",
    "desactivation_dernier_administrateur": "409",
    "desactivation_deja_inactif": "409",
    "desactivation_limite_atteinte": "429",
    "desactivation_erreur_interne": "500",
    "changement_succes": "200",
    "changement_ancien_incorrect": "400",
    "changement_validation": "400",
    "changement_confirmation_invalide": "400",
    "changement_mot_de_passe_identique": "400",
    "changement_champs_inconnus": "400",
    "changement_json_malforme": "400",
    "changement_non_authentifie": "401",
    "changement_jeton_invalide": "401",
    "changement_jeton_expire": "401",
    "changement_methode_interdite": "405",
    "changement_type_contenu": "415",
    "changement_limite_atteinte": "429",
    "changement_erreur_interne": "500",
    "demande_reinitialisation_succes": "200",
    "demande_reinitialisation_email_invalide": "400",
    "demande_reinitialisation_champs_inconnus": "400",
    "demande_reinitialisation_json_malforme": "400",
    "demande_reinitialisation_type_contenu": "415",
    "demande_reinitialisation_methode_interdite": "405",
    "demande_reinitialisation_limite_atteinte": "429",
    "demande_reinitialisation_erreur_interne": "500",
    "confirmation_reinitialisation_succes": "200",
    "confirmation_reinitialisation_jeton_invalide": "400",
    "confirmation_reinitialisation_validation": "400",
    "confirmation_reinitialisation_confirmation_invalide": "400",
    "confirmation_reinitialisation_champs_inconnus": "400",
    "confirmation_reinitialisation_json_malforme": "400",
    "confirmation_reinitialisation_type_contenu": "415",
    "confirmation_reinitialisation_methode_interdite": "405",
    "confirmation_reinitialisation_limite_atteinte": "429",
    "confirmation_reinitialisation_erreur_interne": "500",
    "profil_modification_succes": "200",
    "profil_modification_validation": "400",
    "profil_modification_champs_inconnus": "400",
    "profil_modification_json_malforme": "400",
    "profil_modification_type_contenu": "415",
    "profil_modification_non_authentifie": "401",
    "profil_modification_jeton_invalide": "401",
    "profil_modification_jeton_expire": "401",
    "profil_modification_changement_mot_de_passe_requis": "403",
    "profil_modification_methode_interdite": "405",
    "profil_modification_limite_atteinte": "429",
    "profil_modification_erreur_interne": "500",
}
_CONDITIONS_EXEMPLES = {
    "succes": "Identifiants valides et compte actif.",
    "validation": "Adresse e-mail ou mot de passe invalide.",
    "champs_inconnus": "Le corps contient une propriété non autorisée.",
    "json_malforme": "Le corps application/json est illisible.",
    "identifiants_invalides": "E-mail inconnu, mot de passe faux ou compte inactif.",
    "methode_non_autorisee": "Une méthode autre que POST est appelée.",
    "type_contenu_non_pris_en_charge": "Le corps n’est pas transmis en application/json.",
    "trop_de_requetes": "La limite par IP ou par e-mail est dépassée.",
    "erreur_interne": "Une erreur imprévue survient pendant le traitement.",
    "rafraichissement_succes": "Le refresh est valide et son compte est actif.",
    "rafraichissement_validation": "Le champ refresh est absent, vide ou de type invalide.",
    "rafraichissement_champs_inconnus": "Le corps contient une propriété non autorisée.",
    "rafraichissement_json_malforme": "Le corps application/json est illisible.",
    "rafraichissement_jeton_invalide": "Le jeton est invalide, révoqué ou non autorisé.",
    "rafraichissement_jeton_expire": "Le jeton de rafraîchissement a expiré.",
    "rafraichissement_methode_interdite": "Une méthode autre que POST est appelée.",
    "rafraichissement_type_contenu": "Le corps n’est pas transmis en application/json.",
    "rafraichissement_limite_atteinte": "La limite de renouvellements est dépassée.",
    "rafraichissement_erreur_interne": "Une erreur imprévue survient pendant le traitement.",
    "profil_succes": "Jeton d’accès valide.",
    "profil_sans_connexion": "Jeton valide; aucune connexion précédente.",
    "profil_non_authentifie": "Aucun jeton Bearer n’a été fourni.",
    "profil_jeton_expire": "Le jeton d’accès est expiré.",
    "profil_jeton_invalide": "Le jeton est invalide ou le compte est inactif.",
    "profil_methode_interdite": "Une méthode autre que GET ou PATCH est appelée.",
    "deconnexion_succes": "Le jeton est révoqué; la réponse ne contient aucun corps.",
    "deconnexion_validation": "Le refresh est absent ou vide.",
    "deconnexion_champs_inconnus": "Le corps contient un champ non autorisé.",
    "deconnexion_json_malforme": "Le corps application/json est illisible.",
    "deconnexion_jeton_invalide": "Le refresh est invalide, expiré ou n’est pas un jeton refresh.",
    "deconnexion_non_authentifie": "Aucun jeton d’accès valide n’a été fourni.",
    "deconnexion_acces_invalide": "Le jeton d’accès ne peut pas authentifier la requête.",
    "deconnexion_acces_expire": "Le jeton d’accès est expiré.",
    "deconnexion_jeton_non_autorise": "Le refresh appartient à un autre utilisateur.",
    "deconnexion_methode_interdite": "Une méthode autre que POST est appelée.",
    "deconnexion_type_contenu": "Le corps n’est pas transmis en application/json.",
    "deconnexion_limite_atteinte": "La limite par IP est dépassée.",
    "deconnexion_erreur_interne": "Une erreur imprévue survient pendant le traitement.",
    "creation_succes": "Les données sont valides et l’e-mail n’est pas encore utilisé.",
    "creation_email_invalide": "L’adresse e-mail ne respecte pas le format requis.",
    "creation_mot_de_passe_faible": "Le mot de passe ne respecte pas les validateurs configurés.",
    "creation_role_invalide": "Le rôle n’est ni admin ni vendeur.",
    "creation_champs_inconnus": "Le corps contient une propriété non autorisée.",
    "creation_json_malforme": "Le corps application/json est illisible.",
    "creation_non_authentifie": "Aucun jeton d’accès valide n’a été fourni.",
    "creation_jeton_invalide": "Le jeton d’accès est invalide.",
    "creation_jeton_expire": "Le jeton d’accès est expiré.",
    "creation_acces_interdit": "Le compte authentifié n’est pas administrateur.",
    "creation_changement_mot_de_passe_requis": "Le mot de passe administrateur doit être changé.",
    "creation_methode_interdite": "Une méthode autre que POST est appelée.",
    "creation_email_deja_utilise": "Une contrainte d’unicité a détecté une course.",
    "creation_type_contenu": "Le corps n’est pas transmis en application/json.",
    "creation_limite_atteinte": "La limite par utilisateur est dépassée.",
    "creation_erreur_interne": "Une erreur imprévue survient pendant le traitement.",
    "liste_succes": "Filtre valide, résultats présents, tri et pagination appliqués.",
    "liste_vide": "Les filtres valides ne correspondent à aucun compte.",
    "liste_filtre_invalide": "Une valeur de filtre role ou active est invalide.",
    "liste_tri_invalide": "Le tri demande un champ non autorisé.",
    "liste_non_authentifie": "Aucun jeton d’accès valide n’a été fourni.",
    "liste_jeton_invalide": "Le jeton d’accès est invalide.",
    "liste_jeton_expire": "Le jeton d’accès est expiré.",
    "liste_acces_interdit": "Le compte authentifié n’est pas administrateur.",
    "liste_changement_mot_de_passe_requis": "Le mot de passe administrateur doit être changé.",
    "liste_page_introuvable": "Le numéro de page demandé n’existe pas.",
    "liste_methode_interdite": "Une méthode autre que GET est appelée.",
    "liste_limite_atteinte": "La limite générale par utilisateur est dépassée.",
    "liste_erreur_interne": "Une erreur imprévue survient pendant le traitement.",
    "detail_succes": "Administrateur authentifié; UUID correspondant à un compte.",
    "detail_non_authentifie": "Aucun jeton d’accès valide n’a été fourni.",
    "detail_jeton_invalide": "Le jeton est invalide ou le compte est inactif.",
    "detail_jeton_expire": "Le jeton d’accès est expiré.",
    "detail_acces_interdit": "Un compte non administrateur consulte la route.",
    "detail_changement_mot_de_passe_requis": (
        "L’administrateur doit changer son mot de passe avant cette action."
    ),
    "detail_uuid_invalide": "Le segment ne respecte pas le format UUID.",
    "detail_utilisateur_introuvable": "L’UUID est valide mais aucun compte ne correspond.",
    "detail_methode_interdite": "Une méthode autre que GET est appelée.",
    "detail_limite_atteinte": "La limite générale par utilisateur est dépassée.",
    "detail_erreur_interne": "Une erreur imprévue survient pendant le traitement.",
    "modification_succes": "Les champs autorisés ont été modifiés.",
    "modification_validation": "Une valeur fournie est invalide.",
    "modification_champs_inconnus": "Le corps contient une propriété non modifiable.",
    "modification_json_malforme": "Le corps application/json est illisible.",
    "modification_type_contenu": "Le corps n’est pas transmis en application/json.",
    "modification_non_authentifie": "Aucun jeton d’accès valide n’a été fourni.",
    "modification_jeton_invalide": "Le jeton est invalide ou le compte est inactif.",
    "modification_jeton_expire": "Le jeton d’accès est expiré.",
    "modification_acces_interdit": "Un compte non administrateur appelle la route.",
    "modification_changement_mot_de_passe_requis": (
        "L’administrateur doit changer son mot de passe avant cette action."
    ),
    "modification_role_propre_interdit": "L’administrateur cible son propre compte avec role.",
    "modification_uuid_invalide": "Le segment ne respecte pas le format UUID.",
    "modification_utilisateur_introuvable": ("L’UUID est valide mais aucun compte ne correspond."),
    "modification_methode_interdite": ("Une méthode autre que PATCH est appelée."),
    "modification_email_conflit": "L’adresse e-mail est déjà utilisée.",
    "modification_dernier_administrateur": (
        "La rétrogradation supprimerait le dernier admin actif."
    ),
    "modification_limite_atteinte": "La limite générale par utilisateur est dépassée.",
    "modification_erreur_interne": "Une erreur imprévue survient pendant le traitement.",
    "desactivation_succes": "Le compte est inactif, sans suppression de ses données.",
    "desactivation_corps_interdit": "Un corps non vide est transmis à cette route sans corps.",
    "desactivation_non_authentifie": "Aucun jeton d’accès valide n’a été fourni.",
    "desactivation_jeton_invalide": "Le jeton est invalide ou le compte est inactif.",
    "desactivation_jeton_expire": "Le jeton d’accès est expiré.",
    "desactivation_acces_interdit": "Un compte non administrateur appelle la route.",
    "desactivation_changement_mot_de_passe_requis": (
        "L’administrateur doit changer son mot de passe avant cette action."
    ),
    "desactivation_auto_interdite": "L’administrateur cible son propre compte.",
    "desactivation_uuid_invalide": "Le segment ne respecte pas le format UUID.",
    "desactivation_utilisateur_introuvable": ("L’UUID est valide mais aucun compte ne correspond."),
    "desactivation_methode_interdite": "Une méthode autre que POST est appelée.",
    "desactivation_dernier_administrateur": (
        "La désactivation supprimerait le dernier administrateur actif."
    ),
    "desactivation_deja_inactif": "Le compte ne peut pas être désactivé deux fois.",
    "desactivation_limite_atteinte": "La limite générale par utilisateur est dépassée.",
    "desactivation_erreur_interne": "Une erreur imprévue survient pendant le traitement.",
    "changement_succes": "Ancien mot de passe correct et nouveau secret valide.",
    "changement_ancien_incorrect": "Le mot de passe actuel ne correspond pas au compte.",
    "changement_validation": "Le nouveau secret échoue à un validateur Django.",
    "changement_confirmation_invalide": "La confirmation est différente du nouveau secret.",
    "changement_mot_de_passe_identique": "Le nouveau mot de passe est identique à l’ancien.",
    "changement_champs_inconnus": "Le corps contient un champ non autorisé.",
    "changement_json_malforme": "Le corps application/json est illisible.",
    "changement_non_authentifie": "Aucun jeton d’accès valide n’a été fourni.",
    "changement_jeton_invalide": "Le jeton d’accès est invalide.",
    "changement_jeton_expire": "Le jeton d’accès est expiré.",
    "changement_methode_interdite": "Une méthode autre que POST est appelée.",
    "changement_type_contenu": "Le corps n’est pas transmis en application/json.",
    "changement_limite_atteinte": "La limite horaire par compte est dépassée.",
    "changement_erreur_interne": "Une erreur imprévue survient pendant le traitement.",
    "demande_reinitialisation_succes": "Compte actif, inactif ou inconnu.",
    "demande_reinitialisation_email_invalide": "L’adresse e-mail est mal formée.",
    "demande_reinitialisation_champs_inconnus": "Le corps contient un champ non autorisé.",
    "demande_reinitialisation_json_malforme": "Le corps application/json est illisible.",
    "demande_reinitialisation_type_contenu": "Le corps n’est pas transmis en application/json.",
    "demande_reinitialisation_methode_interdite": "Une méthode autre que POST est appelée.",
    "demande_reinitialisation_limite_atteinte": "La limite par IP ou e-mail est dépassée.",
    "demande_reinitialisation_erreur_interne": (
        "Une erreur imprévue survient pendant le traitement."
    ),
    "confirmation_reinitialisation_succes": "UID et jeton valides, mot de passe conforme.",
    "confirmation_reinitialisation_jeton_invalide": "UID, jeton ou compte inutilisable.",
    "confirmation_reinitialisation_validation": (
        "Le nouveau secret échoue à un validateur Django."
    ),
    "confirmation_reinitialisation_confirmation_invalide": (
        "La confirmation est différente du nouveau secret."
    ),
    "confirmation_reinitialisation_champs_inconnus": "Le corps contient un champ non autorisé.",
    "confirmation_reinitialisation_json_malforme": "Le corps application/json est illisible.",
    "confirmation_reinitialisation_type_contenu": (
        "Le corps n’est pas transmis en application/json."
    ),
    "confirmation_reinitialisation_methode_interdite": ("Une méthode autre que POST est appelée."),
    "confirmation_reinitialisation_limite_atteinte": "La limite horaire par IP est dépassée.",
    "confirmation_reinitialisation_erreur_interne": (
        "Une erreur imprévue survient pendant le traitement."
    ),
    "profil_modification_succes": "Les champs modifiables ont été fournis valablement.",
    "profil_modification_validation": "Le téléphone ne respecte pas le format admis.",
    "profil_modification_champs_inconnus": "Le corps contient un champ non modifiable.",
    "profil_modification_json_malforme": "Le corps application/json est illisible.",
    "profil_modification_type_contenu": "Le corps n’est pas transmis en application/json.",
    "profil_modification_non_authentifie": "Aucun jeton d’accès valide n’a été fourni.",
    "profil_modification_jeton_invalide": "Le jeton d’accès est invalide.",
    "profil_modification_jeton_expire": "Le jeton d’accès est expiré.",
    "profil_modification_changement_mot_de_passe_requis": (
        "Le mot de passe du compte doit être changé."
    ),
    "profil_modification_methode_interdite": "Une méthode autre que PATCH est appelée.",
    "profil_modification_limite_atteinte": "La limite générale par utilisateur est dépassée.",
    "profil_modification_erreur_interne": "Une erreur imprévue survient pendant le traitement.",
}
_ENTETES_EXEMPLES = {
    "succes": "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache",
    "validation": "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache",
    "champs_inconnus": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "json_malforme": ("Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"),
    "identifiants_invalides": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "methode_non_autorisee": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "type_contenu_non_pris_en_charge": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "trop_de_requetes": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "erreur_interne": ("Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"),
    "rafraichissement_succes": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "rafraichissement_validation": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "rafraichissement_champs_inconnus": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "rafraichissement_json_malforme": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "rafraichissement_jeton_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "rafraichissement_jeton_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "rafraichissement_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "rafraichissement_type_contenu": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "rafraichissement_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "rafraichissement_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_succes": "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache",
    "profil_sans_connexion": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_non_authentifie": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_jeton_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_jeton_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_succes": "Cache-Control: no-store; Pragma: no-cache",
    "deconnexion_validation": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_champs_inconnus": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_json_malforme": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_jeton_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_non_authentifie": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_acces_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_acces_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_jeton_non_autorise": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_type_contenu": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "deconnexion_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_succes": "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache",
    "creation_email_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_mot_de_passe_faible": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_role_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_champs_inconnus": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_json_malforme": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_non_authentifie": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_jeton_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_jeton_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_acces_interdit": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_changement_mot_de_passe_requis": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_email_deja_utilise": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_type_contenu": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "creation_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_succes": "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache",
    "liste_vide": "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache",
    "liste_filtre_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_tri_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_non_authentifie": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_jeton_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_jeton_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_acces_interdit": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_changement_mot_de_passe_requis": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_page_introuvable": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "liste_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_succes": "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache",
    "detail_non_authentifie": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_jeton_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_jeton_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_acces_interdit": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_changement_mot_de_passe_requis": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_uuid_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_utilisateur_introuvable": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "detail_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_succes": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_validation": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_champs_inconnus": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_json_malforme": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_type_contenu": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_non_authentifie": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_jeton_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_jeton_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_acces_interdit": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_changement_mot_de_passe_requis": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_role_propre_interdit": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_uuid_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_utilisateur_introuvable": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_email_conflit": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_dernier_administrateur": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "modification_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_succes": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_corps_interdit": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_non_authentifie": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_jeton_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_jeton_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_acces_interdit": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_changement_mot_de_passe_requis": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_auto_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_uuid_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_utilisateur_introuvable": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_dernier_administrateur": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_deja_inactif": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "desactivation_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_succes": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_ancien_incorrect": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_validation": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_confirmation_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_mot_de_passe_identique": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_champs_inconnus": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_json_malforme": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_non_authentifie": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_jeton_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_jeton_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_type_contenu": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "changement_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "demande_reinitialisation_succes": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "demande_reinitialisation_email_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "demande_reinitialisation_champs_inconnus": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "demande_reinitialisation_json_malforme": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "demande_reinitialisation_type_contenu": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "demande_reinitialisation_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "demande_reinitialisation_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "demande_reinitialisation_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_succes": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_jeton_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_validation": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_confirmation_invalide": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_champs_inconnus": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_json_malforme": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_type_contenu": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "confirmation_reinitialisation_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_succes": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_validation": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_champs_inconnus": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_json_malforme": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_type_contenu": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_non_authentifie": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_jeton_invalide": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_jeton_expire": (
        "Content-Type: application/json; WWW-Authenticate: Bearer; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_changement_mot_de_passe_requis": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_methode_interdite": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_limite_atteinte": (
        "Content-Type: application/json; Retry-After: secondes; "
        "Cache-Control: no-store; Pragma: no-cache"
    ),
    "profil_modification_erreur_interne": (
        "Content-Type: application/json; Cache-Control: no-store; Pragma: no-cache"
    ),
}


def exemples_openapi_connexion(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI depuis le catalogue canonique."""
    return [
        OpenApiExample(
            name=noms[0] if len(noms) == 1 else nom,
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_CONNEXION[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemple_requete_openapi_connexion() -> OpenApiExample:
    """Construit l’exemple de requête à partir du catalogue canonique."""
    return OpenApiExample(
        name="Requête de connexion",
        summary="Identifiants de connexion",
        value=EXEMPLE_REQUETE_CONNEXION,
        request_only=True,
    )


def exemple_requete_openapi_rafraichissement() -> OpenApiExample:
    """Construit l’exemple de requête de renouvellement depuis le catalogue."""
    return OpenApiExample(
        name="Requête de renouvellement",
        summary="Jeton de rafraîchissement à renouveler",
        value=EXEMPLE_REQUETE_RAFRAICHISSEMENT,
        request_only=True,
    )


def exemple_requete_openapi_deconnexion() -> OpenApiExample:
    """Construit l’exemple de requête de déconnexion depuis le catalogue."""
    return OpenApiExample(
        name="Requête de déconnexion",
        summary="Jeton de rafraîchissement à révoquer",
        value=EXEMPLE_REQUETE_DECONNEXION,
        request_only=True,
    )


def exemple_requete_openapi_creation_utilisateur() -> OpenApiExample:
    """Construit l’exemple de création utilisateur depuis le catalogue."""
    return OpenApiExample(
        name="Requête de création d’utilisateur",
        summary="Données du compte et mot de passe temporaire",
        value=EXEMPLE_REQUETE_CREATION_UTILISATEUR,
        request_only=True,
    )


def exemples_openapi_rafraichissement(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de renouvellement depuis le catalogue."""
    return [
        OpenApiExample(
            name=nom.removeprefix("rafraichissement_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_RAFRAICHISSEMENT[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemples_openapi_deconnexion(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de déconnexion depuis le catalogue."""
    return [
        OpenApiExample(
            name=nom.removeprefix("deconnexion_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_DECONNEXION[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemples_openapi_creation_utilisateur(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de création utilisateur."""
    return [
        OpenApiExample(
            name=nom.removeprefix("creation_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_CREATION_UTILISATEUR[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemples_openapi_liste_utilisateurs(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de liste utilisateur."""
    return [
        OpenApiExample(
            name=nom.removeprefix("liste_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_LISTE_UTILISATEURS[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemples_openapi_detail_utilisateur(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI du détail utilisateur."""
    return [
        OpenApiExample(
            name=nom.removeprefix("detail_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_DETAIL_UTILISATEUR[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemples_openapi_modification_utilisateur(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de modification utilisateur."""
    return [
        OpenApiExample(
            name=nom.removeprefix("modification_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_MODIFICATION_UTILISATEUR[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemples_openapi_desactivation_utilisateur(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de désactivation utilisateur."""
    return [
        OpenApiExample(
            name=nom.removeprefix("desactivation_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_DESACTIVATION_UTILISATEUR[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemple_requete_openapi_changement_mot_de_passe() -> OpenApiExample:
    """Construit l’exemple de requête de changement de mot de passe."""
    return OpenApiExample(
        name="Requête de changement de mot de passe",
        summary="Ancien mot de passe et nouveau secret confirmé",
        value=EXEMPLE_REQUETE_CHANGEMENT_MOT_DE_PASSE,
        request_only=True,
    )


def exemples_openapi_changement_mot_de_passe(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de changement de mot de passe."""
    return [
        OpenApiExample(
            name=nom.removeprefix("changement_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_CHANGEMENT_MOT_DE_PASSE[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemple_requete_openapi_demande_reinitialisation() -> OpenApiExample:
    """Construit l’exemple de requête de demande de réinitialisation."""
    return OpenApiExample(
        name="Requête de demande de réinitialisation",
        summary="Adresse e-mail du compte",
        value={"email": "rakoto@exemple.com"},
        request_only=True,
    )


def exemples_openapi_demande_reinitialisation(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de demande de réinitialisation."""
    return [
        OpenApiExample(
            name=nom.removeprefix("demande_reinitialisation_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_DEMANDE_REINITIALISATION[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemple_requete_openapi_confirmation_reinitialisation() -> OpenApiExample:
    """Construit l’exemple de requête de confirmation de réinitialisation."""
    return OpenApiExample(
        name="Requête de confirmation de réinitialisation",
        summary="UUID, jeton et nouveau mot de passe confirmé",
        value=EXEMPLE_REQUETE_CONFIRMATION_REINITIALISATION,
        request_only=True,
    )


def exemples_openapi_confirmation_reinitialisation(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de confirmation de réinitialisation."""
    return [
        OpenApiExample(
            name=nom.removeprefix("confirmation_reinitialisation_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_CONFIRMATION_REINITIALISATION[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemple_requete_openapi_modification_profil() -> OpenApiExample:
    """Construit l’exemple de requête de modification du profil."""
    return OpenApiExample(
        name="Requête de modification du profil",
        summary="Champs de profil modifiables",
        value=EXEMPLE_REQUETE_MODIFICATION_PROFIL,
        request_only=True,
    )


def exemples_openapi_modification_profil(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI de modification du profil."""
    return [
        OpenApiExample(
            name=nom.removeprefix("profil_modification_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_MODIFICATION_PROFIL[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]


def exemples_openapi_profil(*noms: str) -> list[OpenApiExample]:
    """Construit les exemples OpenAPI du profil depuis le catalogue canonique."""
    return [
        OpenApiExample(
            name=nom.removeprefix("profil_"),
            summary=_METADONNEES_EXEMPLES[nom][0],
            description=_METADONNEES_EXEMPLES[nom][1],
            value=EXEMPLES_JSON_PROFIL[nom],
            response_only=True,
            status_codes=[_CODES_HTTP_EXEMPLES[nom]],
        )
        for nom in noms
    ]
