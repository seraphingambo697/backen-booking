from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from app.modules.user.domain.entities.user import User
from app.modules.user.infrastructure.repositories.user_repository_impl import DjangoUserRepository

def get_current_user(request) -> User:
    auth = JWTAuthentication()
    try:
        validated = auth.authenticate(request)
        if validated is None:
            raise AuthenticationFailed("Token manquant.")
        user_model, _ = validated
    except Exception as exc:
        raise AuthenticationFailed(str(exc))
    user = DjangoUserRepository().find_by_id(str(user_model.id))
    if not user or not user.is_active:
        raise AuthenticationFailed("Compte introuvable ou désactivé.")
    return user

def require_admin(request) -> User:
    user = get_current_user(request)
    if not user.is_admin:
        raise PermissionDenied("Droits administrateur requis.")
    return user
