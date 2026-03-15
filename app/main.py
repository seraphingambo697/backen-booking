"""app/main.py — URLs racines LuxStay"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include([
        path("auth/",         include("app.modules.user.presentation.api.v1.auth")),
        path("users/",        include("app.modules.user.presentation.api.v1.users")),
        path("hotels/",       include("app.modules.hotel.presentation.api.v1.hotels")),
        path("bookings/",     include("app.modules.booking.presentation.api.v1.bookings")),
        path("payments/",     include("app.modules.payment.presentation.api.v1.payments")),
        path("reviews/",      include("app.modules.review.presentation.api.v1.reviews")),
        path("search/",       include("app.modules.search.presentation.api.v1.search")),
    ])),
    path("api/schema/", SpectacularAPIView.as_view(),                      name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/",  SpectacularRedocView.as_view(url_name="schema"),   name="redoc"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)