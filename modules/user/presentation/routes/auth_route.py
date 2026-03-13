
from django.urls import path
from modules.user.presentation.controller.auth import LoginView, LogoutView, RegisterView
from rest_framework_simplejwt.views import TokenRefreshView



urlpatterns = [
    path("register", RegisterView.as_view(),     name="auth-register"),
    path("login",    LoginView.as_view(),         name="auth-login"),
    path("logout",   LogoutView.as_view(),        name="auth-logout"),
    path("refresh",  TokenRefreshView.as_view(),  name="auth-refresh"),
]