"""
app/core/config/production.py
Settings de production.

- PostgreSQL obligatoire
- DEBUG = False
- Sécurité renforcée (HTTPS, HSTS, cookies sécurisés)
- Logs vers fichier + console

Usage : DJANGO_SETTINGS_MODULE=app.core.config.production

Variables .env requises en prod :
    SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST,
    ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS
"""
from decouple import config, Csv

from app.core.config.base import *  # noqa: F401, F403

DEBUG = False

SECRET_KEY = config("SECRET_KEY")  

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

# ── PostgreSQL ──────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     config("DB_NAME"),
        "USER":     config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST":     config("DB_HOST", default="localhost"),
        "PORT":     config("DB_PORT", default="5432"),
        "OPTIONS": {
            "connect_timeout": 10,
            "sslmode": config("DB_SSLMODE", default="prefer"),
        },
        "CONN_MAX_AGE": 60,  # Connexions persistantes (performances)
    }
}

# CORS
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# ── HTTPS / Sécurité headers
SECURE_SSL_REDIRECT              = True
SECURE_HSTS_SECONDS              = 31_536_000   # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS   = True
SECURE_HSTS_PRELOAD              = True
SECURE_PROXY_SSL_HEADER          = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE            = True
CSRF_COOKIE_SECURE               = True
SESSION_COOKIE_HTTPONLY          = True
CSRF_COOKIE_HTTPONLY             = True

LOGGING["handlers"]["file"] = {          
    "class":    "logging.handlers.RotatingFileHandler",
    "filename": "/var/log/luxstay/app.log",
    "maxBytes": 10 * 1024 * 1024,        
    "backupCount": 5,
    "formatter": "verbose",
}
LOGGING["loggers"]["app"] = {            
    "handlers":  ["console", "file"],
    "level":     "INFO",
    "propagate": False,
}
LOGGING["loggers"]["django.request"] = { 
    "handlers":  ["console", "file"],
    "level":     "ERROR",
    "propagate": False,
}

# ── Email SMTP (Sendgrid / AWS SES / etc.) ─────────────────────────────────────
EMAIL_BACKEND= "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS  = True
EMAIL_HOST_USER     = config("EMAIL_HOST_USER", default="apikey")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL  = config("DEFAULT_FROM_EMAIL",  default="noreply@luxstay.fr")
