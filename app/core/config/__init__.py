"""
app/core/config/__init__.py
Point d'entrée de la configuration.

Sélectionne automatiquement le bon settings selon l'environnement.
Peut être utilisé directement comme DJANGO_SETTINGS_MODULE.

Ordre de priorité :
  1. Variable DJANGO_SETTINGS_MODULE déjà définie sur un sous-module → respectée
  2. Variable APP_ENV  : development | production | testing
  3. Défaut            : development

"""
import os

_ENV_MAP = {
    "development": "app.core.config.development",
    "production":  "app.core.config.production",
    "testing":     "app.core.config.testing",
    "test":        "app.core.config.testing",
}

_current = os.environ.get("DJANGO_SETTINGS_MODULE", "")
if not _current or _current == "app.core.config":
    _app_env = os.environ.get("APP_ENV", "development").lower()
    _target  = _ENV_MAP.get(_app_env, "app.core.config.development")
    os.environ["DJANGO_SETTINGS_MODULE"] = _target
