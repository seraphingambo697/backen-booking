# Akkor Hotel — Backend API

> Backend Django REST Framework pour la plateforme de réservation hôtelière **Akkor Hotel Ltd**.
>
> **Stack :** Python 3.11+ · Django 5.0 · Django REST Framework · JWT · SQLite (dev) · PostgreSQL (prod)

---

## Sommaire

1. [Prérequis](#1-prérequis)
2. [Installation](#2-installation)
3. [Configuration — Variables d'environnement](#3-configuration--variables-denvironnement)
4. [Base de données et Migrations](#4-base-de-données-et-migrations)
5. [Lancer le serveur](#5-lancer-le-serveur)
6. [Données de démonstration](#6-données-de-démonstration)
7. [Tests](#7-tests)
8. [Documentation API Swagger](#8-documentation-api-swagger)
9. [Référence des endpoints](#9-référence-des-endpoints)
10. [CI/CD Pipeline GitHub Actions](#10-cicd-pipeline-github-actions)
11. [Architecture du projet](#11-architecture-du-projet)
12. [Dépannage](#12-dépannage)

---

## 1. Prérequis

Vérifier que ces outils sont installés **avant** de commencer.

### Obligatoires

| Outil | Version minimale | Commande de vérification |
|-------|-----------------|--------------------------|
| **Python** | 3.11 | `python --version` |
| **pip** | 23.0 | `pip --version` |
| **Git** | 2.x | `git --version` |

### Optionnels (production uniquement)

| Outil | Utilisation |
|-------|-------------|
| **PostgreSQL** 14+ | Base de données en production |
| **Docker** 24+ | Déploiement via image conteneurisée |
| **Gunicorn** | Serveur WSGI de production |

> En développement, **SQLite est utilisé automatiquement** — aucune base de données externe n'est nécessaire.

---

## 2. Installation

### Étape 1 — Cloner le dépôt

```bash
git clone https://github.com/akkor-hotel/backend.git
cd backend
```

Après le `cd backend`, vous devez voir cette structure à la racine :

```
backend/
├── manage.py          ← point d'entrée de toutes les commandes Django
├── requirements.txt   ← dépendances Python
├── pytest.ini         ← configuration des tests
├── .env.example       ← modèle de variables d'environnement
├── conftest.py        ← fixtures de tests partagées
├── Dockerfile
└── app/               ← code source de l'application
```

> **Important :** toutes les commandes de ce README (`python manage.py ...`, `pytest`, etc.) se lancent depuis ce dossier `backend/`, là où se trouve `manage.py`.

### Étape 2 — Créer un environnement virtuel Python

```bash
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
# Linux / macOS :
source .venv/bin/activate

# Windows (PowerShell) :
.venv\Scripts\Activate.ps1

# Windows (CMD) :
.venv\Scripts\activate.bat
```

> L'invite de commande doit maintenant afficher `(.venv)` en début de ligne.

### Étape 3 — Installer les dépendances Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Liste complète des paquets installés :

| Paquet | Version | Rôle |
|--------|---------|------|
| `django` | 5.0.4 | Framework web |
| `djangorestframework` | 3.15.1 | API REST |
| `djangorestframework-simplejwt` | 5.3.1 | Authentification JWT (access + refresh tokens) |
| `django-cors-headers` | 4.3.1 | Gestion des en-têtes CORS |
| `django-filter` | 24.2 | Filtres dynamiques sur les endpoints list |
| `drf-spectacular` | 0.27.2 | Génération automatique Swagger / OpenAPI 3.0 |
| `django-extensions` | 3.2.3 | Commandes Django supplémentaires |
| `Pillow` | 10.3.0 | Traitement des images uploadées |
| `python-decouple` | 3.8 | Lecture des variables d'environnement depuis `.env` |
| `pytest` | 8.2.0 | Runner de tests |
| `pytest-django` | 4.8.0 | Intégration Django pour pytest |
| `pytest-cov` | 5.0.0 | Rapport de couverture de code |
| `factory-boy` | 3.3.0 | Factories de données pour les tests |
| `faker` | 25.0.0 | Génération de données fictives réalistes |
| `black` | 24.4.2 | Formateur de code automatique |
| `isort` | 5.13.2 | Tri automatique des imports |
| `flake8` | 7.0.0 | Linter PEP8 |

### Étape 4 — Créer le fichier d'environnement

```bash
cp .env.example .env
```

Ouvrir `.env` et renseigner au minimum la variable `SECRET_KEY` (voir section 3).

---

## 3. Configuration — Variables d'environnement

Toutes les variables sont lues depuis le fichier `.env` à la racine du projet via `python-decouple`. Ce fichier ne doit **jamais** être commité dans Git.

### Variables obligatoires

| Variable | Description | Générer une valeur sécurisée |
|----------|-------------|------------------------------|
| `SECRET_KEY` | Clé secrète Django — doit être longue et aléatoire | `python -c "import secrets; print(secrets.token_hex(50))"` |

### Environnement

| Variable | Défaut | Valeurs possibles | Description |
|----------|--------|-------------------|-------------|
| `APP_ENV` | `development` | `development` / `production` / `testing` | Sélectionne automatiquement le fichier de config Django |
| `DEBUG` | `True` | `True` / `False` | Mode debug (mettre `False` en production) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Liste séparée par virgules | Hôtes autorisés à servir l'application |

### Base de données

**Développement (SQLite — rien à configurer) :**

Le fichier `luxstay_dev.db` est créé automatiquement à la racine du projet.

**Production (PostgreSQL) :**

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DB_ENGINE` | Backend Django | `django.db.backends.postgresql` |
| `DB_NAME` | Nom de la base | `akkor_hotel` |
| `DB_USER` | Utilisateur PostgreSQL | `akkor` |
| `DB_PASSWORD` | Mot de passe PostgreSQL | `motdepasse_securise` |
| `DB_HOST` | Hôte du serveur PostgreSQL | `localhost` |
| `DB_PORT` | Port PostgreSQL | `5432` |

### JWT

| Variable | Défaut | Description |
|----------|--------|-------------|
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `60` | Durée de vie du token d'accès en minutes |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | Durée de vie du refresh token en jours |

### CORS

| Variable | Défaut | Description |
|----------|--------|-------------|
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Origines frontend autorisées, séparées par des virgules |

> Ports couverts par défaut : `3000` (Create React App), `5173` (Vite dev), `4173` (Vite preview).

### Réservations

| Variable | Défaut | Description |
|----------|--------|-------------|
| `BOOKING_FREE_CANCEL_HOURS` | `48` | Délai minimum (heures) avant check-in pour bénéficier d'une annulation gratuite |
| `BOOKING_MAX_NIGHTS` | `30` | Durée maximum autorisée d'un séjour en nuits |
| `BOOKING_PENDING_EXPIRY_MINUTES` | `30` | Délai avant expiration automatique d'une réservation non payée |

### Paiement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `PAYMENT_PROVIDER` | `mock` | Provider de paiement (`mock` en dev — remplacer par `stripe` en prod) |
| `MOCK_PAYMENT_SUCCESS_RATE` | `0.95` | Taux de succès simulé du paiement mock (entre `0.0` et `1.0`) |

### Fichier `.env` complet (exemple)

```dotenv
# ── Obligatoire ─────────
SECRET_KEY=remplacez-par-une-cle-tres-longue-et-aleatoire

# ── Environnement ───────
APP_ENV=development
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# ── JWT ─────────────────
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# ── CORS ────────────────
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# ── Paiement ────────────
PAYMENT_PROVIDER=mock
MOCK_PAYMENT_SUCCESS_RATE=0.95

# ── Réservations ────────
BOOKING_FREE_CANCEL_HOURS=48
BOOKING_MAX_NIGHTS=30
BOOKING_PENDING_EXPIRY_MINUTES=30
```

---

## 4. Base de données et Migrations

> **Où lancer ces commandes ?**
> Toutes les commandes `python manage.py ...` se lancent **depuis le dossier `backend/`**, c'est-à-dire le dossier où se trouve le fichier `manage.py`.
>
> ```
> backend/          ← vous devez être ici
> ├── manage.py     ← c'est ce fichier qui est appelé
> ├── requirements.txt
> ├── .env
> └── app/
> ```
>
> Si vous venez de cloner le projet :
> ```bash
> cd backend       # se placer dans le bon dossier
> ls               # vous devez voir manage.py dans la liste
> ```

### Appliquer les migrations (obligatoire au premier lancement)

```bash
python manage.py migrate
```

Cette commande crée toutes les tables nécessaires. En développement, le fichier `luxstay_dev.db` (SQLite) est créé automatiquement à la racine — aucune base de données externe n'est requise.

### Vérifier l'état des migrations

```bash
python manage.py showmigrations
```

### Créer les migrations après modification d'un modèle

```bash
python manage.py makemigrations
python manage.py migrate
```

### Créer un super-utilisateur Django admin (optionnel)

```bash
python manage.py createsuperuser
```

L'interface d'administration est accessible sur `http://localhost:8000/admin/`.

---

## 5. Lancer le serveur

### Développement (serveur Django intégré)

```bash
python manage.py runserver
```

Le serveur démarre sur **http://localhost:8000**.


Pour écouter sur toutes les interfaces (accès depuis un autre appareil sur le réseau) :

```bash
python manage.py runserver 0.0.0.0:8000
```

### Avec l'environnement explicitement défini

```bash
APP_ENV=development python manage.py runserver
```

## 6. Données de démonstration


### Comptes créés

| Email | Mot de passe | Rôle |
|-------|-------------|------|
| `admin@akkor.com ` | `AdminPass123!` | Administrateur (accès total) |
| `seraphin@gmail.com` | `12345678#` | Utilisateur standard |

### Données créées

- 2 hôtels (Le Grand Palais Paris · Hôtel Riviera Nice)
- 3 chambres réparties sur ces hôtels

---

## 7. Tests

La suite de tests utilise **pytest** avec une base SQLite en mémoire — aucune configuration supplémentaire n'est requise.

### Lancer tous les tests

```bash
pytest
```

### Tests unitaires uniquement (aucune DB, ultra-rapides)

```bash
pytest -k "not integration"
```

### Tests d'intégration uniquement (DB SQLite en mémoire)

```bash
pytest -k "integration"
```

### Tests d'un module spécifique

```bash
# Tous les tests du module user
pytest app/modules/user/tests/ -v

# Tous les tests du module booking
pytest app/modules/booking/tests/ -v

# Value objects partagés
pytest app/shared/tests/ -v

# Un seul fichier
pytest app/modules/user/tests/unit/test_user_entity.py -v
```

### Avec rapport de couverture de code

```bash
# Rapport dans le terminal
pytest --cov=app --cov-report=term-missing

# Rapport HTML (ouvre coverage-html/index.html dans le navigateur)
pytest --cov=app --cov-report=html
open coverage-html/index.html   # macOS
xdg-open coverage-html/index.html  # Linux

# Les deux simultanément
pytest --cov=app --cov-report=term-missing --cov-report=html
```

### Résumé des fichiers de test

| Fichier | Type | Couverture |
|---------|------|------------|
| `shared/tests/test_value_objects.py` | Unitaire | `DateRange`, `Money`, `GuestCount` |
| `shared/tests/test_base_entity.py` | Unitaire | `BaseEntity`, domain events |
| `modules/user/tests/unit/test_user_entity.py` | Unitaire | Entité `User`, 5 use cases |
| `modules/hotel/tests/unit/test_hotel_entity.py` | Unitaire | Entités `Hotel`, `Room` |
| `modules/hotel/tests/unit/test_hotel_use_cases.py` | Unitaire | Use cases hotel |
| `modules/booking/tests/unit/test_booking_entity.py` | Unitaire | Entité `Booking`, machine à états |
| `modules/booking/tests/unit/test_booking_use_cases.py` | Unitaire | Use cases booking |
| `modules/user/tests/integration/test_user_api.py` | Intégration | Auth register/login/logout, profil |
| `modules/hotel/tests/integration/test_hotel_api.py` | Intégration | CRUD hôtels, autorisations |
| `modules/booking/tests/integration/test_booking_api.py` | Intégration | CRUD réservations, conflits, annulation |
| `modules/search/tests/integration/test_search_api.py` | Intégration | Recherche multi-critères |

### Vérifier la qualité du code

```bash
# Vérifier le formatage (sans modifier)
black --check app/

# Appliquer le formatage automatiquement
black app/

# Vérifier l'ordre des imports
isort --check-only app/

# Corriger l'ordre des imports
isort app/

# Linter PEP8
flake8 app/ --max-line-length=120 --exclude=migrations,__pycache__
```

---

## 8. Documentation API Swagger

Une fois le serveur lancé, la documentation interactive est disponible directement dans le navigateur.

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api/docs/` | **Swagger UI** — interface interactive pour tester les endpoints |
| `http://localhost:8000/api/redoc/` | **ReDoc** — documentation lisible, bien formatée |
| `http://localhost:8000/api/schema/` | Schéma OpenAPI brut (JSON) |

### Tester un endpoint protégé dans Swagger UI

1. Ouvrir `http://localhost:8000/api/docs/`
2. Appeler `POST /api/v1/auth/login/` avec les identifiants demo
3. Dans la réponse, copier la valeur du champ `data.tokens.access`
4. Cliquer sur **Authorize** (bouton en haut à droite de la page)
5. Dans le champ, saisir exactement : `Bearer <valeur_copiée>`
6. Cliquer **Authorize** — tous les cadenas passent au vert
7. Les endpoints protégés sont maintenant accessibles

---

## 9. Référence des endpoints

Tous les endpoints sont préfixés par `/api/v1/`.

### Auth

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `POST` | `/auth/register/` | Non | Créer un compte |
| `POST` | `/auth/login/` | Non | Se connecter — retourne `access` + `refresh` |
| `POST` | `/auth/logout/` | Oui | Invalider le refresh token |
| `POST` | `/auth/refresh/` | Non | Renouveler l'access token |

### Utilisateurs

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/users/me/` | Oui | Lire son profil |
| `PATCH` | `/users/me/` | Oui | Modifier son profil |
| `DELETE` | `/users/me/` | Oui | Supprimer son compte |

### Hôtels

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/hotels/` | Non | Lister (filtrable, paginé) |
| `POST` | `/hotels/` | Admin | Créer un hôtel |
| `GET` | `/hotels/{id}/` | Non | Détail |
| `PATCH` | `/hotels/{id}/` | Admin | Modifier |
| `DELETE` | `/hotels/{id}/` | Admin | Désactiver (soft delete) |
| `GET` | `/hotels/{id}/rooms/` | Non | Chambres d'un hôtel |
| `POST` | `/hotels/{id}/rooms/` | Admin | Ajouter une chambre |
| `GET` | `/hotels/{id}/rooms/{rid}/` | Non | Détail d'une chambre |
| `PATCH` | `/hotels/{id}/rooms/{rid}/` | Admin | Modifier une chambre |

**Paramètres de filtre sur `GET /hotels/` :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `city` | string | Filtrer par ville (`?city=Paris`) |
| `stars` | int | Étoiles minimum (`?stars=4`) |
| `page` | int | Numéro de page (défaut : 1) |
| `page_size` | int | Résultats par page (défaut : 12) |

### Recherche

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `POST` | `/search/` | Non | Rechercher des hôtels disponibles |

```json
{
  "city": "Paris",
  "check_in": "2025-12-20",
  "check_out": "2025-12-23",
  "guest_count": 2,
  "stars_min": 4,
  "price_max": 300.0,
  "amenities": ["WiFi", "Piscine"]
}
```

### Réservations

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `POST` | `/bookings/availability/` | Non | Chambres disponibles |
| `GET` | `/bookings/` | Oui | Mes réservations (`?status=PENDING`) |
| `POST` | `/bookings/` | Oui | Créer une réservation |
| `GET` | `/bookings/{id}/` | Oui | Détail |
| `DELETE` | `/bookings/{id}/` | Oui | Annuler |
| `POST` | `/bookings/{id}/confirm/` | Oui | Confirmer après paiement |

**Statuts possibles :**

| Statut | Description |
|--------|-------------|
| `PENDING` | Créée, en attente de paiement |
| `CONFIRMED` | Payée et confirmée |
| `CANCELLED` | Annulée |
| `COMPLETED` | Séjour terminé |

### Paiements

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `POST` | `/payments/pay/` | Oui | Payer une réservation |
| `GET` | `/payments/{id}/` | Oui | Détail d'un paiement |
| `POST` | `/payments/refund/{booking_id}/` | Oui | Rembourser |

### Avis

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/reviews/?hotel_id={id}` | Non | Avis d'un hôtel |
| `POST` | `/reviews/` | Oui | Laisser un avis |
| `DELETE` | `/reviews/{id}/` | Oui | Supprimer un avis |

### Format standard des réponses

**Succès :**
```json
{
  "success": true,
  "data": { "id": "...", "..." : "..." }
}
```

**Liste paginée :**
```json
{
  "success": true,
  "count": 42,
  "data": [ { "..." : "..." } ]
}
```

**Erreur :**
```json
{
  "success": false,
  "error": {
    "code": "booking_conflict",
    "message": "Cette chambre est déjà réservée pour ces dates.",
    "details": {}
  }
}
```

### Codes HTTP

| Code | Signification |
|------|--------------|
| `200` | OK |
| `201` | Créé |
| `204` | Succès sans contenu |
| `400` | Requête invalide |
| `401` | Non authentifié |
| `402` | Paiement échoué |
| `403` | Accès refusé |
| `404` | Introuvable |
| `409` | Conflit (dates, email déjà utilisé…) |
| `422` | Règle métier violée |

---

## 10. CI/CD Pipeline GitHub Actions

Deux pipelines sont configurés dans `.github/workflows/`.

### Pull Request — `pr.yml`

Déclenché sur chaque PR vers `main` ou `develop`.

```
Lint & Format  →  Tests unitaires  →  Tests d'intégration
```

Le merge est **bloqué automatiquement** si un job échoue. En plus, GitHub doit être configuré pour exiger au minimum **1 approbation** et **0 commentaire ouvert** avant de pouvoir merger.

### Merge sur main — `main.yml`

Déclenché automatiquement à chaque push sur `main`.

```
Tests complets  →  Tests frontend + E2E Cypress
       ↓
Audit sécurité (bandit + pip-audit + npm audit)
       ↓
Build image Docker  →  Push sur GitHub Container Registry
       ↓
Deploy (simulé avec echo + résumé dans GitHub Actions)
```

### Configurer la protection de branche GitHub

Dans le dépôt GitHub : **Settings → Branches → Add branch protection rule**

- **Branch name pattern :** `main`
- Cocher **Require a pull request before merging**
- **Require approvals :** `1`
- Cocher **Dismiss stale pull request approvals when new commits are pushed**
- Cocher **Require status checks to pass before merging**
- Ajouter les status checks requis : `Lint & Format`, `Unit Tests`, `Integration Tests`
- Cocher **Require conversation resolution before merging**
- Cocher **Do not allow bypassing the above settings**

---

## 11. Architecture du projet

```
backend/
├── manage.py                   # Point d'entrée CLI Django
├── pytest.ini                  # Configuration pytest
├── requirements.txt            # Dépendances Python
├── .env.example                # Modèle de configuration
├── conftest.py                 # Fixtures pytest partagées
├── Dockerfile                  # Image de production
├── .github/
│   └── workflows/
│       ├── pr.yml              # Pipeline Pull Request
│       └── main.yml            # Pipeline Main (prod)
└── app/
    ├── core/                   # Noyau : configuration, sécurité, exceptions
    │   ├── config/
    │   │   ├── __init__.py     # Sélection auto de l'environnement
    │   │   ├── base.py         # Settings communs
    │   │   ├── development.py  # Dev : SQLite, DEBUG=True, logs verbeux
    │   │   ├── production.py   # Prod : PostgreSQL, HTTPS, email SMTP
    │   │   └── testing.py      # Tests : SQLite :memory:, MD5 password
    │   ├── dependencies/       # Factories use cases (injection de dépendances)
    │   │   ├── booking.py
    │   │   ├── hotel.py
    │   │   ├── payment.py
    │   │   ├── review.py
    │   │   ├── search.py
    │   │   └── user.py
    │   ├── exceptions.py       # Hiérarchie complète des DomainException
    │   ├── security.py         # PasswordHasher (bcrypt) + TokenService (JWT)
    │   └── database.py         # atomic_transaction(), @transactional
    ├── shared/                 # Abstractions réutilisables par tous les modules
    │   ├── domain/
    │   │   ├── base_entity.py      # BaseEntity + DomainEvents
    │   │   ├── base_repository.py  # Interface CRUD abstraite
    │   │   ├── base_use_case.py    # Contrat BaseUseCase[Input, Output]
    │   │   └── value_objects.py    # DateRange, Money, GuestCount
    │   ├── infrastructure/
    │   │   ├── database/
    │   │   │   ├── base_repository_impl.py  # Implémentation Django générique
    │   │   │   └── transactional.py         # Décorateur @transactional
    │   │   └── external/
    │   │       └── base_gateway.py          # Interface PaymentGateway ABC
    │   └── presentation/
    │       ├── middleware.py   # Exception handler DRF + RequestLoggingMiddleware
    │       ├── pagination.py   # StandardPagination + BookingPagination (cursor)
    │       └── responses.py    # success(), created(), no_content(), error()…
    └── modules/
        ├── user/               # Gestion des comptes + Auth JWT
        ├── hotel/              # Hôtels et chambres
        ├── booking/            # Réservations avec Value Objects
        ├── payment/            # Paiements (mock, Stripe-ready)
        ├── review/             # Avis voyageurs
        └── search/             # Recherche hôtels multi-critères
```

**Chaque module suit le pattern Clean Architecture :**

```
module/
├── domain/
│   ├── entities/       # Dataclasses + règles métier + validations
│   ├── repositories/   # Interfaces abstraites (ABC)
│   └── use_cases/      # Cas d'utilisation (1 classe = 1 action)
├── infrastructure/
│   ├── database/       # Modèles ORM Django + AppConfig
│   └── repositories/   # Implémentations concrètes Django
└── presentation/
    ├── api/v1/         # Vues DRF (APIView) + urlpatterns inline
    └── schemas/        # Sérialiseurs DRF (request + response)
```

---

## 12. Dépannage

### `ModuleNotFoundError: No module named 'app'`

L'environnement virtuel n'est pas activé ou les dépendances manquent.

```bash
# Activer l'environnement
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate.bat       # Windows

# Réinstaller les dépendances
pip install -r requirements.txt
```

### `ImproperlyConfigured: The SECRET_KEY setting must not be empty`

Le fichier `.env` n'existe pas ou `SECRET_KEY` est absent.

```bash
cp .env.example .env
# Éditer .env et renseigner SECRET_KEY
```

### `OperationalError: no such table: ...`

Les migrations n'ont pas été appliquées.

```bash
python manage.py migrate
```

### `Address already in use` au démarrage

Un autre processus occupe le port 8000.

```bash
# Utiliser un autre port
python manage.py runserver 8001

# Ou libérer le port 8000
# Linux/macOS :
lsof -ti:8000 | xargs kill -9
# Windows :
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### `AppRegistryNotReady` dans les tests

Vérifier que `pytest.ini` contient :

```ini
[pytest]
DJANGO_SETTINGS_MODULE = app.core.config.testing
```

### `401 Unauthorized` sur tous les endpoints

Le token JWT a expiré (durée de vie : 60 minutes par défaut). Le renouveler :

```bash
POST /api/v1/auth/refresh/
Content-Type: application/json

{ "refresh": "<votre_refresh_token>" }
```

La réponse contient un nouvel `access` token à utiliser dans le header `Authorization: Bearer <token>`.

### Les tests d'intégration échouent avec des erreurs de FK

Vérifier que les fixtures `conftest.py` créent bien les objets dans le bon ordre (`admin_user` avant `sample_hotel`, `sample_hotel` avant `sample_room`). Les fixtures pytest s'enchaînent automatiquement via les paramètres de fonction.

---

## Licence

MIT — Akkor Hotel Ltd © 2025
