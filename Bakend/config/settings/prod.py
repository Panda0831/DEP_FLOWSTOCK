"""Configuration de production avec contrôles stricts."""

from . import base
from .base import env

for nom_parametre in dir(base):
    if nom_parametre.isupper():
        globals()[nom_parametre] = getattr(base, nom_parametre)

DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACTIVER_DOCUMENTATION_API = env.bool("ACTIVER_DOCUMENTATION_API", default=False)

if not base.ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS doit être configuré en production.")

url_cache = env.str("CACHE_URL", default="")
if not url_cache:
    raise ValueError("CACHE_URL doit désigner un cache partagé en production.")
CACHES = {"default": env.cache_url("CACHE_URL")}
