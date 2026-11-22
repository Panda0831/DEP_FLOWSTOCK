"""Configuration isolée pour les tests."""

from .base import *  # noqa: F403

DEBUG = False
DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
AXES_ENABLED = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
ACTIVER_DOCUMENTATION_API = True
