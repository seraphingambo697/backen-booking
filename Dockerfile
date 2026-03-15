FROM python:3.12-slim

# Métadonnées
LABEL org.opencontainers.image.title="Akkor Hotel API"
LABEL org.opencontainers.image.description="Backend Django — Akkor Hotel Ltd"
LABEL org.opencontainers.image.source="https://github.com/akkor-hotel/backend"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8000

WORKDIR /app

# Dépendances système (Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn psycopg2-binary

# Code source
COPY . .

# Collecter les fichiers statiques
RUN APP_ENV=production SECRET_KEY=build-only \
    python manage.py collectstatic --noinput --settings=app.core.config.production || true

# Utilisateur non-root
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE $PORT

# Démarrage avec Gunicorn
CMD ["sh", "-c", \
    "python manage.py migrate --settings=app.core.config.production && \
     gunicorn app.wsgi:application \
       --bind 0.0.0.0:$PORT \
       --workers 4 \
       --worker-class sync \
       --timeout 120 \
       --access-logfile - \
       --error-logfile -"]
