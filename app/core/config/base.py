"""
app/core/config/base.py
Settings Django communs à TOUS les environnements.

Ne contient jamais de valeurs sensibles hardcodées.
Chaque environnement (dev/prod/test) hérite de cette base
et surcharge uniquement ce qui change.
"""
from datetime import timedelta
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent 

# ── Sécurité ────────────
SECRET_KEY = config("SECRET_KEY", default="django-insecure-base-key-override-me")
ALLOWED_HOSTS: list[str] = []

# ── Applications 
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_extensions",
]

# Modules LuxStay — AppConfig de chaque couche infrastructure
LOCAL_APPS = [
    "app.modules.user.infrastructure.database.apps.UserInfraConfig",
    "app.modules.hotel.infrastructure.database.apps.HotelInfraConfig",
    "app.modules.booking.infrastructure.database.apps.BookingInfraConfig",
    "app.modules.payment.infrastructure.database.apps.PaymentInfraConfig",
    "app.modules.review.infrastructure.database.apps.ReviewInfraConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ──────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "app.shared.presentation.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "app.main"
WSGI_APPLICATION = "app.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# ── Modèle User personnalisé
AUTH_USER_MODEL = "user_infrastructure.UserModel"

# ── DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "app.shared.presentation.pagination.StandardPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "app.shared.presentation.middleware.custom_exception_handler",
}

# ── JWT ──────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=60, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

CORS_ALLOWED_ORIGINS: list[str] = []

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL   = "/media/"
MEDIA_ROOT  = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SPECTACULAR_SETTINGS = {
    "TITLE": "LuxStay API",
    "DESCRIPTION": "Backend LuxStay",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} — {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django":          {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.request":  {"handlers": ["console"], "level": "ERROR",   "propagate": False},
        "app":             {"handlers": ["console"], "level": "INFO",    "propagate": False},
    },
}

# ── Paiement 
PAYMENT_PROVIDER = config("PAYMENT_PROVIDER", default="mock")
MOCK_PAYMENT_SUCCESS_RATE = config("MOCK_PAYMENT_SUCCESS_RATE", default=0.95, cast=float)

# ── Booking 
# Délai minimum (heures) avant check_in pour annulation gratuite
BOOKING_FREE_CANCEL_HOURS     = config("BOOKING_FREE_CANCEL_HOURS",     default=48,  cast=int)

# Nombre maximum de nuits par réservation
BOOKING_MAX_NIGHTS = config("BOOKING_MAX_NIGHTS",            default=30,  cast=int)
# Délai avant expiration d'une réservation PENDING non payée
BOOKING_PENDING_EXPIRY_MINUTES = config("BOOKING_PENDING_EXPIRY_MINUTES", default=30, cast=int)
