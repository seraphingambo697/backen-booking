"""
app/core/security.py
Sécurité : hashing mot de passe + génération tokens JWT.

Équivalent du core/security.py FastAPI (python-jose → SimpleJWT).
"""
import logging

from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger("app")


class PasswordHasher:
    """Encapsule le hashing Django (PBKDF2 par défaut, bcrypt si configuré)."""

    @staticmethod
    def hash(plain_password: str) -> str:
        return make_password(plain_password)

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        return check_password(plain_password, hashed_password)


class TokenService:
    """
    Génère et invalide les paires de tokens JWT via SimpleJWT.
    Utilisé par les use cases d'authentification.
    """

    @staticmethod
    def generate_tokens(user_id: str) -> dict:
        """Retourne {'access': '...', 'refresh': '...'}."""
        from app.modules.user.infrastructure.database.user_models import UserModel
        try:
            user = UserModel.objects.get(id=user_id)
            refresh = RefreshToken.for_user(user)
            return {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        except UserModel.DoesNotExist:
            logger.error(f"generate_tokens: user {user_id} introuvable")
            raise ValueError(f"User {user_id} introuvable")

    @staticmethod
    def blacklist_token(refresh_token_str: str) -> None:
        """Révoque un refresh token (logout)."""
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
        except Exception as exc:
            logger.warning(f"blacklist_token error: {exc}")
            raise ValueError("Token invalide ou déjà révoqué")