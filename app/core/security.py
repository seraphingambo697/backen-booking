"""
app/core/security.py
Sécurité : hashing de mots de passe + gestion des tokens JWT.

Deux classes distinctes avec responsabilités claires :
  - PasswordHasher  : hashing/vérification des mots de passe
  - TokenService    : génération/révocation des tokens JWT

Aucune dépendance vers les modules métier — utilisable partout dans le projet.
"""
import logging

from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger("app")


class PasswordHasher:
    """
    Encapsule le hashing Django.

    Avantage : swapper l'algo (PBKDF2 → bcrypt → argon2) sans toucher
    au code appelant — il suffit de modifier PASSWORD_HASHERS dans les settings.
    """

    @staticmethod
    def hash(plain_password: str) -> str:
        """Retourne le mot de passe hashé avec l'algo configuré dans settings."""
        return make_password(plain_password)

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """
        Retourne True si le mot de passe correspond au hash.
        Constant-time comparison — résistant aux timing attacks.
        """
        return check_password(plain_password, hashed_password)


class TokenService:
    """
    Gestion des tokens JWT via SimpleJWT.

    Fournit une interface propre pour :
      - Générer une paire access/refresh
      - Rafraîchir un access token
      - Révoquer (blacklister) un refresh token au logout
    """

    @staticmethod
    def generate_tokens(user_id: str) -> dict[str, str]:
        """
        Génère access/refresh token pour l'utilisateur donné.

        """
        from app.modules.user.infrastructure.database.user_models import UserModel

        try:
            user    = UserModel.objects.get(id=user_id)
            refresh = RefreshToken.for_user(user)
            return {
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
            }
        except UserModel.DoesNotExist:
            logger.error(f"TokenService: user {user_id} introuvable")
            raise ValueError(f"Utilisateur {user_id} introuvable.")

    @staticmethod
    def blacklist_token(refresh_token_str: str) -> None:
        """
        Révoque un refresh token (logout).
        Requiert rest_framework_simplejwt.token_blacklist dans INSTALLED_APPS.
        """
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
            logger.info("Refresh token blacklisté avec succès.")
        except TokenError as e:
            logger.warning(f"TokenService.blacklist: {e}")
            raise ValueError("Token invalide ou déjà révoqué.")

    @staticmethod
    def decode_user_id(access_token_str: str) -> str:
        """
        Extrait le user_id d'un access token sans passer par DRF.
        Utile pour les consumers WebSocket ou les tâches async.
        """
        try:
            token = AccessToken(access_token_str)
            return str(token["user_id"])
        except TokenError as e:
            raise ValueError(f"Token invalide : {e}")
