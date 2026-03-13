"""Auth endpoints : register, login, logout, refresh"""
from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.core.dependencies import get_create_user_uc, get_authenticate_user_uc
from app.core.security import TokenService
from app.modules.user.domain.use_cases.create_user import CreateUserInput
from app.modules.user.domain.use_cases.get_user import AuthenticateUserInput
from app.modules.user.presentation.schemas.user_schemas import (
    RegisterRequestSerializer, LoginRequestSerializer,
    TokenResponseSerializer, UserResponseSerializer,
)


def _u(user): return UserResponseSerializer(user).data


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=RegisterRequestSerializer, responses={201: UserResponseSerializer},
                   summary="Créer un compte", tags=["Auth"])
    def post(self, request):
        s = RegisterRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        user = get_create_user_uc().execute(CreateUserInput(
            email=d["email"], first_name=d["first_name"], last_name=d["last_name"],
            password=d["password"], phone=d.get("phone", ""),
        ))
        return Response(_u(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=LoginRequestSerializer, responses={200: TokenResponseSerializer},
                   summary="Se connecter", tags=["Auth"])
    def post(self, request):
        s = LoginRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        user = get_authenticate_user_uc().execute(AuthenticateUserInput(
            email=d["email"], password=d["password"],
        ))
        tokens = TokenService.generate_tokens(user.id)
        return Response({**tokens, "user": _u(user)})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]


    @extend_schema(responses={204: None}, summary="Se déconnecter", tags=["Auth"])
    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            TokenService.blacklist_token(refresh)
        return Response(status=status.HTTP_204_NO_CONTENT)

