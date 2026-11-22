"""Limites de débit des opérations d’authentification et d’administration."""

from rest_framework.exceptions import ParseError, UnsupportedMediaType

from apps.core.reseau import adresse_ip_client
from apps.core.throttling import LimitationParCleStable


class ConnexionParAdresseIP(LimitationParCleStable):
    """Limite les tentatives selon l’adresse réelle du client."""

    scope = "connexion"

    def cle_client(self, requete) -> str | None:
        return adresse_ip_client(requete._request)


class ConnexionParEmail(LimitationParCleStable):
    """Limite les tentatives par e-mail normalisé, qu’un compte existe ou non."""

    scope = "connexion_par_email"

    def get_cache_key(self, requete, vue) -> str | None:
        try:
            cle = self.cle_client(requete)
        except ParseError as erreur:
            vue.erreur_analyse_connexion = erreur
            return None
        except UnsupportedMediaType as erreur:
            vue.erreur_analyse_connexion = erreur
            return None
        return self.cle_cache(cle)

    def cle_client(self, requete) -> str | None:
        donnees = requete.data
        if not isinstance(donnees, dict):
            return None
        email = donnees.get("email")
        if not isinstance(email, str):
            return None

        adresse = email.strip().lower()
        return adresse if adresse and len(adresse) <= 254 else None


class DeconnexionParAdresseIP(LimitationParCleStable):
    """Limite les tentatives de déconnexion selon l’adresse réelle du client."""

    scope = "deconnexion"

    def cle_client(self, requete) -> str | None:
        return adresse_ip_client(requete._request)


class CreationUtilisateurParAdministrateur(LimitationParCleStable):
    """Limite les créations de compte pour chaque administrateur authentifié."""

    scope = "creation_utilisateur"

    def cle_client(self, requete) -> str | None:
        utilisateur = requete.user
        if not utilisateur.is_authenticated:
            return None
        return str(utilisateur.pk)


class ReinitialisationParAdresseIP(LimitationParCleStable):
    """Limite les demandes de réinitialisation selon l’adresse réseau."""

    scope = "reinitialisation_demande"

    def cle_client(self, requete) -> str | None:
        return adresse_ip_client(requete._request)


class ReinitialisationParEmail(LimitationParCleStable):
    """Limite les demandes selon l’empreinte de l’e-mail normalisé."""

    scope = "reinitialisation_demande_par_email"

    def get_cache_key(self, requete, vue) -> str | None:
        try:
            return self.cle_cache(self.cle_client(requete))
        except ParseError as erreur:
            vue.erreur_analyse_reinitialisation = erreur
            return None
        except UnsupportedMediaType as erreur:
            vue.erreur_analyse_reinitialisation = erreur
            return None

    def cle_client(self, requete) -> str | None:
        donnees = requete.data
        if not isinstance(donnees, dict):
            return None
        email = donnees.get("email")
        if not isinstance(email, str):
            return None
        return email.strip().lower() or None


class ChangementMotDePasseParUtilisateur(LimitationParCleStable):
    """Limite les changements de mot de passe par compte authentifié."""

    scope = "changement_mot_de_passe"

    def cle_client(self, requete) -> str | None:
        utilisateur = requete.user
        if not utilisateur.is_authenticated:
            return None
        return str(utilisateur.pk)


class ConfirmationReinitialisationParAdresseIP(LimitationParCleStable):
    """Limite les confirmations de réinitialisation selon l’adresse réseau."""

    scope = "reinitialisation_confirmation"

    def cle_client(self, requete) -> str | None:
        return adresse_ip_client(requete._request)


class ProfilParUtilisateur(LimitationParCleStable):
    """Limite les lectures et modifications du profil par compte connecté."""

    scope = "user"

    def cle_client(self, requete) -> str | None:
        utilisateur = requete.user
        if not utilisateur.is_authenticated:
            return None
        return str(utilisateur.pk)


class RafraichissementParAdresseIP(LimitationParCleStable):
    """Limite les renouvellements par adresse réelle du client."""

    scope = "rafraichissement"

    def cle_client(self, requete) -> str | None:
        return adresse_ip_client(requete._request)
