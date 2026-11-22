"""Configuration de développement."""

from . import base
from .base import env

for nom_parametre in dir(base):
    if nom_parametre.isupper():
        globals()[nom_parametre] = getattr(base, nom_parametre)

DEBUG = env.bool("DEBUG", default=False)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
ACTIVER_DOCUMENTATION_API = env.bool("ACTIVER_DOCUMENTATION_API", default=True)
