"""
app/core/config/testing.py
Settings pour la suite de tests pytest.

- SQLite en mémoire (ultra-rapide, isolation parfaite)
- DEBUG = False (comportement proche de la prod)

Usage automatique via pytest.ini :
    DJANGO_SETTINGS_MODULE = app.core.config.testing
"""
from app.core.config.base import *  

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",              
        "TEST": {"NAME": ":memory:"},
    }
}

SECRET_KEY = "test-secret-key-not-for-production"
ALLOWED_HOSTS = ["*"]

# ── Performances
# Désactive le hashing bcrypt (trop lent) — utilise MD5 pour les tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ── Désactive les logs pendant les tests 
LOGGING["root"]["level"] = "CRITICAL"           
LOGGING["loggers"]["app"]["level"] = "CRITICAL" # 

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

MOCK_PAYMENT_SUCCESS_RATE = 1.0  

import tempfile
MEDIA_ROOT = tempfile.mkdtemp()

CORS_ALLOWED_ORIGINS = ["http://testserver"]
