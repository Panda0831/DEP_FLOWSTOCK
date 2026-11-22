"""Lecture prudente des adresses IP derrière des proxys de confiance."""

import ipaddress

from django.conf import settings
from django.http import HttpRequest


def adresse_ip_client(requete: HttpRequest) -> str | None:
    """Retourne l’adresse cliente sans faire confiance à un X-Forwarded-For non configuré."""
    adresse_distante = requete.META.get("REMOTE_ADDR")
    nombre_proxies = settings.REST_FRAMEWORK["NUM_PROXIES"]

    if not nombre_proxies:
        return _normaliser_adresse(adresse_distante)

    adresses_transferees = requete.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
    adresses_transferees = [adresse.strip() for adresse in adresses_transferees if adresse.strip()]

    if len(adresses_transferees) <= nombre_proxies:
        return _normaliser_adresse(adresse_distante)

    return _normaliser_adresse(adresses_transferees[-nombre_proxies - 1])


def _normaliser_adresse(adresse: str | None) -> str | None:
    if not adresse:
        return None

    try:
        return str(ipaddress.ip_address(adresse))
    except ValueError:
        return None
