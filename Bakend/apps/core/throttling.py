"""Points d’extension communs pour les limites de débit."""

import hashlib
import re

from django.core.exceptions import ImproperlyConfigured
from rest_framework.settings import api_settings
from rest_framework.throttling import SimpleRateThrottle


class LimitationParCleStable(SimpleRateThrottle):
    """Base de limitation qui dérive une clé stable sans conserver de valeur brute."""

    scope = "cle_stable"

    def get_rate(self) -> str:
        """Relit les taux DRF courants pour respecter les réglages temporaires."""
        try:
            return api_settings.DEFAULT_THROTTLE_RATES[self.scope]
        except KeyError as erreur:
            raise ImproperlyConfigured(
                f"Aucun taux de limitation configuré pour « {self.scope} »."
            ) from erreur

    def parse_rate(self, rate: str | None) -> tuple[int | None, int | None]:
        """Accepte les périodes DRF et les multiples comme « 15min »."""
        if rate is None:
            return None, None

        correspondance = re.fullmatch(
            r"(?P<nombre_requetes>\d+)/(?:(?P<multiple>\d+))?"
            r"(?P<unite>s|sec|min|m|hour|h|day|d)",
            rate,
        )
        if correspondance is None:
            raise ImproperlyConfigured(f"Limite de débit invalide : {rate}")

        durées = {
            "s": 1,
            "sec": 1,
            "m": 60,
            "min": 60,
            "h": 3600,
            "hour": 3600,
            "d": 86400,
            "day": 86400,
        }
        multiple = int(correspondance["multiple"] or 1)
        duree = multiple * durées[correspondance["unite"]]
        return int(correspondance["nombre_requetes"]), duree

    def get_cache_key(self, requete, vue) -> str | None:
        """Retourne une clé dérivée, ou aucune si la vue n’expose pas d’identifiant."""
        return self.cle_cache(self.cle_client(requete))

    def cle_cache(self, cle: str | None) -> str | None:
        """Construit une clé de cache qui ne contient pas l’identifiant brut."""
        if not cle:
            return None
        empreinte = hashlib.sha256(cle.encode("utf-8")).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": empreinte}

    def cle_client(self, requete) -> str | None:
        """Fournit la clé de limitation à implémenter par une sous-classe."""
        raise NotImplementedError
