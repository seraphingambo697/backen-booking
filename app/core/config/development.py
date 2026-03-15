"""
Settings de développement local.
"""
from decouple import config

from app.core.config.base import *  

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "luxstay_dev.db",  
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  
    "http://localhost:4173",   
    "http://127.0.0.1:5173",
]

# ── Logs détaillés 
LOGGING["loggers"]["app"]["level"] = "DEBUG"       
LOGGING["loggers"]["django"]["level"] = "INFO"   
LOGGING["root"]["level"] = "INFO"           

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
