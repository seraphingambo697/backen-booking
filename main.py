"""
app/main.py
URLs racines Django — équivalent du main.py FastAPI (include_router).

Chaque module enregistre ses propres URLs via include().
Ce fichier agrège sans connaître le contenu des routes.
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # ── API v1 ───────────────────────────────────────────────────────────────
    path("api/v1/", include([
        path("users/",  include("app.modules.user.presentation.api.v1.users")),
    ])),

    # ── Documentation OpenAPI ─────────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(),                       name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"),  name="swagger-ui"),
    path("api/redoc/",  SpectacularRedocView.as_view(url_name="schema"),    name="redoc"),
]