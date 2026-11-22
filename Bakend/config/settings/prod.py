"""Configuration de production."""

from .base import *  # noqa: F403
from .base import ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS, DATABASES, DEBUG, env

if DEBUG:
    raise RuntimeError("DEBUG doit être désactivé en production")
if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS doit être configuré en production")
if not DATABASES["default"]["ENGINE"].endswith("postgresql"):
    raise RuntimeError("DATABASE_URL doit désigner une base PostgreSQL en production")
if CORS_ALLOWED_ORIGINS and not CSRF_TRUSTED_ORIGINS:
    raise RuntimeError("CSRF_TRUSTED_ORIGINS est requis lorsque CORS_ALLOWED_ORIGINS est configuré")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = env.str("SESSION_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_SAMESITE = env.str("CSRF_COOKIE_SAMESITE", default="Lax")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31_536_000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REDIRECT_EXEMPT = ["healthz/"]

# An explicit allow-list prevents a browser hosted on another origin from
# calling the authenticated API unless that origin is configured at deploy time.
CORS_ALLOW_CREDENTIALS = bool(CORS_ALLOWED_ORIGINS)
