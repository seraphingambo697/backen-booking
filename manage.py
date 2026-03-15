#!/usr/bin/env python
"""manage.py — Point d'entrée Django CLI."""
import os
import sys


def main():
    # Sélectionne le bon fichier de settings selon APP_ENV
    # APP_ENV peut être défini dans .env ou en variable d'environnement shell
    _env = os.environ.get("APP_ENV", "development").lower()
    _map = {
        "development": "app.core.config.development",
        "production":  "app.core.config.production",
        "testing":     "app.core.config.testing",
        "test":        "app.core.config.testing",
    }
    _settings = _map.get(_env, "app.core.config.development")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", _settings)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django introuvable. Activez votre virtualenv et lancez : pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
