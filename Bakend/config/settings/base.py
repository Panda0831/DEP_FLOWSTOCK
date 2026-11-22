"""Configuration commune de Django et de l’API StockFlow."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]
env = environ.Env()
env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
JWT_CLE_SIGNATURE = env("JWT_CLE_SIGNATURE")
if len(JWT_CLE_SIGNATURE) < 50 or JWT_CLE_SIGNATURE == SECRET_KEY:
    raise ValueError("JWT_CLE_SIGNATURE doit être distincte et contenir au moins 50 caractères.")

DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
NOMBRE_PROXIES_DE_CONFIANCE = env.int("NOMBRE_PROXIES_DE_CONFIANCE", default=0)
if NOMBRE_PROXIES_DE_CONFIANCE < 0:
    raise ValueError("NOMBRE_PROXIES_DE_CONFIANCE ne peut pas être négatif.")
LANGUAGE_CODE = "fr"
TIME_ZONE = "Indian/Antananarivo"
USE_I18N = True
USE_TZ = True
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.Utilisateur"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.CacheNoStoreMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

if env.str("BASE_DE_DONNEES_URL", default=""):
    DATABASES = {"default": env.db_url("BASE_DE_DONNEES_URL")}
    if not DATABASES["default"]["ENGINE"].endswith("postgresql"):
        raise ValueError("BASE_DE_DONNEES_URL doit utiliser PostgreSQL.")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": env("BDD_HOTE"),
            "PORT": env("BDD_PORT", default="5432"),
            "NAME": env("BDD_NOM"),
            "USER": env("BDD_UTILISATEUR"),
            "PASSWORD": env("BDD_MOT_DE_PASSE"),
            "CONN_MAX_AGE": 60,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("email", "nom", "prenom")},
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "apps.core.validators.LongueurMaximaleMotDePasseValidator",
    },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
PASSWORD_RESET_TIMEOUT = 3600

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "apps.accounts.permissions.ChangementMotDePasseNonRequis",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.PaginationStandard",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.gestionnaire_exceptions",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "120/min",
        "connexion": "10/min",
        "connexion_par_email": "5/15min",
        "rafraichissement": "30/min",
        "deconnexion": "30/min",
        "creation_utilisateur": "30/min",
        "reinitialisation_demande": "5/hour",
        "reinitialisation_demande_par_email": "3/hour",
        "reinitialisation_confirmation": "10/hour",
        "changement_mot_de_passe": "5/hour",
    },
    "NUM_PROXIES": NOMBRE_PROXIES_DE_CONFIANCE,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": JWT_CLE_SIGNATURE,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "uuid",
    "USER_ID_CLAIM": "utilisateur_uuid",
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "stockflow-dev",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env("EMAIL_FROM", default="StockFlow <noreply@localhost>")
URL_FRONTEND_REINITIALISATION = env("URL_FRONTEND_REINITIALISATION", default="")
ACTIVER_DOCUMENTATION_API = env.bool("ACTIVER_DOCUMENTATION_API", default=False)

STATIC_URL = "static/"
LOGIN_URL = "/admin/login/"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SPECTACULAR_SETTINGS = {
    "TITLE": "API StockFlow",
    "DESCRIPTION": "API de gestion des comptes et de l’authentification StockFlow.",
    "VERSION": "1.0.0",
    "LANGUAGE_CODE": "fr",
    "SERVE_INCLUDE_SCHEMA": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "securite": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "securite",
        },
        "fichier_securite": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(BASE_DIR / "logs" / "securite.log"),
            "maxBytes": 5_000_000,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "securite",
        },
    },
    "loggers": {
        "stockflow.securite": {
            "handlers": ["console", "fichier_securite"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
