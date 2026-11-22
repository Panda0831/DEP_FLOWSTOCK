"""Configuration dédiée aux tests PostgreSQL."""

from . import base
from .base import env

for nom_parametre in dir(base):
    if nom_parametre.isupper():
        globals()[nom_parametre] = getattr(base, nom_parametre)

DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
base.DATABASES["default"]["USER"] = env("BDD_TEST_UTILISATEUR")
base.DATABASES["default"]["PASSWORD"] = env("BDD_TEST_MOT_DE_PASSE")
base.CACHES["default"] = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "stockflow-tests",
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
ACTIVER_DOCUMENTATION_API = True
