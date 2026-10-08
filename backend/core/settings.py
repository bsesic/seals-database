"""
Django settings for the Seals Database.

Single monolithic settings module driven by environment variables (django-environ).
Production hardening lives in the ``if not DEBUG:`` block at the bottom.
"""

import sys
from pathlib import Path

import environ
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Environment -----------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# --- Applications ----------------------------------------------------------
INSTALLED_APPS = [
    # Unfold admin theme (must precede django.contrib.admin).
    "unfold",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",
    "unfold.contrib.simple_history",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    # Third party
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "corsheaders",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_vite",
    "taggit",
    "simple_history",
    "waffle",
    "import_export",
    "actstream",
    "djangordf",
    # Authentication (allauth)
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.mfa",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.microsoft",
    "allauth.socialaccount.providers.apple",
    "allauth.socialaccount.providers.facebook",
    # Local
    "users",
    "organizations",
    "pages",
    "catalog",
    "documents",
    "notifications",
    "compliance",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # allauth
    "allauth.account.middleware.AccountMiddleware",
    # Sets request.organization for the current tenant (must come after auth).
    "organizations.middleware.OrganizationMiddleware",
    # Audit-log request user + feature flags.
    "simple_history.middleware.HistoryRequestMiddleware",
    "waffle.middleware.WaffleMiddleware",
]

SITE_ID = env.int("DJANGO_SITE_ID", default=1)

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "organizations.context_processors.organizations",
                "notifications.context_processors.notifications",
                "core.context_processors.analytics",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# --- Database --------------------------------------------------------------
# Supports DATABASE_URL (preferred) and individual DB_* variables as a fallback.
if env("DATABASE_URL", default=""):
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": env("DB_ENGINE", default="django.db.backends.postgresql"),
            "NAME": env("DB_NAME", default="saas"),
            "USER": env("DB_USER", default="saas"),
            "PASSWORD": env("DB_PASSWORD", default="saas"),
            "HOST": env("DB_HOST", default="127.0.0.1"),
            "PORT": env("DB_PORT", default="5432"),
        }
    }
DATABASES["default"].setdefault("CONN_MAX_AGE", env.int("DB_CONN_MAX_AGE", default=60))
DATABASES["default"].setdefault("CONN_HEALTH_CHECKS", True)

# --- Authentication --------------------------------------------------------
AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- allauth ---------------------------------------------------------------
LOGIN_REDIRECT_URL = "/profile/"
LOGOUT_REDIRECT_URL = "/"

ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]
# "mandatory" (default), "optional" or "none". Relax to "none"/"optional" for a
# single-user / internal deployment or before an SMTP relay is configured.
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="mandatory")
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_LOGOUT_ON_GET = False

# Rate limits on auth endpoints (allauth's built-in throttling).
ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/5m",
    "signup": "10/h",
    "reset_password": "5/h",
}

# Two-factor authentication (allauth.mfa)
MFA_SUPPORTED_TYPES = ["totp", "recovery_codes"]

# Social providers: an APP is only registered when its env credentials are set,
# so unconfigured providers never show a broken button.
SOCIALACCOUNT_PROVIDERS = {}
for _provider in ("google", "microsoft", "apple", "facebook"):
    _prefix = _provider.upper()
    _client_id = env(f"{_prefix}_CLIENT_ID", default="")
    _secret = env(f"{_prefix}_SECRET", default="")
    if _client_id and _secret:
        _app = {"client_id": _client_id, "secret": _secret, "key": ""}
        if _provider == "apple":
            # Apple also needs the key id (secret), team id (key) and the .p8 contents.
            _app["key"] = env("APPLE_KEY_ID", default="")
            _app["settings"] = {"certificate_key": env("APPLE_CERTIFICATE_KEY", default="")}
        SOCIALACCOUNT_PROVIDERS[_provider] = {"APPS": [_app]}

# --- Crispy forms ----------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# --- Compliance ------------------------------------------------------------
# Grace period before a deactivated (soft-deleted) account is hard-deleted by
# the purge_deleted_accounts management command.
ACCOUNT_DELETION_GRACE_DAYS = env.int("ACCOUNT_DELETION_GRACE_DAYS", default=30)

# --- Privacy analytics -----------------------------------------------------
# Set ANALYTICS_PROVIDER to "plausible" or "matomo" to enable a script tag.
ANALYTICS_PROVIDER = env("ANALYTICS_PROVIDER", default="")
PLAUSIBLE_DOMAIN = env("PLAUSIBLE_DOMAIN", default="")
PLAUSIBLE_SRC = env("PLAUSIBLE_SRC", default="https://plausible.io/js/script.js")
MATOMO_URL = env("MATOMO_URL", default="")
MATOMO_SITE_ID = env("MATOMO_SITE_ID", default="")

# --- Internationalization --------------------------------------------------
LANGUAGE_CODE = env("DJANGO_LANGUAGE_CODE", default="en")
TIME_ZONE = env("DJANGO_TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]
LANGUAGES = [
    ("en", _("English")),
    ("de", _("German")),
]

# --- Static & media --------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Object storage for user uploads (S3-compatible: R2, B2, Hetzner, AWS).
# Defaults to local filesystem; set USE_S3=True to switch.
if env.bool("USE_S3", default=False):
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="") or None
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="") or None
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="") or None
    AWS_QUERYSTRING_AUTH = env.bool("AWS_QUERYSTRING_AUTH", default=False)
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

# --- Vite asset pipeline ---------------------------------------------------
# In dev (DEBUG) django-vite points at the Vite dev server (run `npm run dev`).
# In production it reads the manifest produced by `npm run build`.
DJANGO_VITE = {
    "default": {
        "dev_mode": DEBUG,
        "dev_server_port": 5173,
        "static_url_prefix": "dist",
        "manifest_path": BASE_DIR / "static" / "dist" / ".vite" / "manifest.json",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Cache (Redis, opt-in) -------------------------------------------------
if env.bool("USE_REDIS_CACHE", default=False):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/0"),
        }
    }

# --- Email -----------------------------------------------------------------
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# Transactional vs. marketing senders. allauth and app notifications use the
# transactional sender; bulk/marketing sends should use a separate from-address
# (and ideally a separate backend/API key) to protect deliverability.
TRANSACTIONAL_FROM_EMAIL = env("TRANSACTIONAL_FROM_EMAIL", default="") or DEFAULT_FROM_EMAIL
MARKETING_FROM_EMAIL = env("MARKETING_FROM_EMAIL", default="") or DEFAULT_FROM_EMAIL

# --- CORS ------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:8080", "http://localhost:3000"],
)

# --- Django REST Framework -------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "1000/hour"},
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "ALLOWED_VERSIONS": ["v1"],
    "DEFAULT_VERSION": "v1",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Seals Database API",
    "DESCRIPTION": "Public REST API for the Seals Database catalogue of stamp "
    "and cylinder seals, bullae and inscriptions from the Southern Levant.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# allauth headless: JSON auth endpoints for SPA/mobile (session + app tokens).
HEADLESS_ONLY = False

# --- Search ----------------------------------------------------------------
# "database" = Postgres full-text search (default, no extra infra).
# "elasticsearch" = use an Elasticsearch cluster at ELASTICSEARCH_URL.
SEARCH_BACKEND = env("SEARCH_BACKEND", default="database")
ELASTICSEARCH_URL = env("ELASTICSEARCH_URL", default="http://127.0.0.1:9200")
ELASTICSEARCH_INDEX = env("ELASTICSEARCH_INDEX", default="documents")
ELASTICSEARCH_CATALOG_INDEX = env("ELASTICSEARCH_CATALOG_INDEX", default="catalog-artefacts")

# --- RDF / Linked Open Data (djangordf) ------------------------------------
# Base URI for minted resource IRIs (dereferenceable — the artefact web URL).
RDF_BASE_URI = env("RDF_BASE_URI", default="http://localhost:8000")

# Triple-store backend. Default is an in-memory rdflib store (dev/tests). Set
# FUSEKI_ENDPOINT (e.g. http://localhost:3030/seals) to sync to Apache Jena
# Fuseki over SPARQL 1.1, which then provides the public SPARQL endpoint.
_fuseki_endpoint = env("FUSEKI_ENDPOINT", default="")
if _fuseki_endpoint:
    DJANGORDF_BACKEND = {
        "class": "djangordf.backends.fuseki.FusekiBackend",
        "endpoint": _fuseki_endpoint,
    }
    if env("FUSEKI_USER", default=""):
        DJANGORDF_BACKEND["user"] = env("FUSEKI_USER")
        DJANGORDF_BACKEND["password"] = env("FUSEKI_PASSWORD", default="")
else:
    DJANGORDF_BACKEND = {"class": "djangordf.backends.memory.InMemoryBackend"}

DJANGORDF_DEFAULT_NAMESPACE = RDF_BASE_URI.rstrip("/") + "/id/"
DJANGORDF_DEFAULT_GRAPH = RDF_BASE_URI.rstrip("/") + "/graph/catalog"
DJANGORDF_NAMESPACES = {
    "crm": "http://www.cidoc-crm.org/cidoc-crm/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
}

# --- Activity stream -------------------------------------------------------
ACTSTREAM_SETTINGS = {
    "USE_JSONFIELD": True,
    "FETCH_RELATIONS": True,
}

# --- Unfold admin theme ----------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "Seals Database",
    "SITE_HEADER": "Seals Database",
    "SITE_SUBHEADER": _("Administration"),
}

# --- Celery ----------------------------------------------------------------
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default=env("REDIS_URL", default="redis://127.0.0.1:6379/0")
)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True
# Run tasks synchronously under pytest so the suite never blocks on a broker/
# worker (config_from_object reads these at app finalize, which would otherwise
# reset a per-test override back to the env default).
if "pytest" in sys.modules:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE

# --- Production security hardening -----------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 365)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

# --- Error tracking (Sentry) -----------------------------------------------
# Enabled only when SENTRY_DSN is set. The Django integration is auto-enabled
# by sentry-sdk[django]. deploy.sh exports SENTRY_RELEASE (the git short SHA).
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env("SENTRY_ENVIRONMENT", default="production"),
        release=env("SENTRY_RELEASE", default=""),
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        send_default_pii=False,
    )
