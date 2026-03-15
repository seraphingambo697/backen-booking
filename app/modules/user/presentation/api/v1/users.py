"""User profile endpoints"""
from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from app.core.dependencies import get_update_user_uc, get_delete_user_uc
from app.core.dependencies.user import get_list_users_uc, get_user_uc
from app.core.exceptions import AuthorizationError
from app.modules.user.domain.use_cases.get_user import GetUserInput
from app.modules.user.domain.use_cases.update_user import UpdateUserInput
from app.modules.user.domain.use_cases.delete_user import DeleteUserInput
from app.modules.user.presentation.api.dependencies import get_current_user
from app.modules.user.presentation.schemas.user_schemas import (
    UpdateUserRequestSerializer, UserResponseSerializer,
)
from app.shared.presentation.responses import success, no_content, success_list


def _u(user):
    return UserResponseSerializer(user).data


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserResponseSerializer},
        summary="Mon profil",
        tags=["Users"],
    )
    def get(self, request):
        return success(_u(get_current_user(request)))

    @extend_schema(
        request=UpdateUserRequestSerializer,
        responses={200: UserResponseSerializer},
        summary="Modifier mon profil",
        tags=["Users"],
    )
    def patch(self, request):
        user = get_current_user(request)
        s    = UpdateUserRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d    = s.validated_data
        updated = get_update_user_uc().execute(
            UpdateUserInput(user_id=user.id, **{k: v for k, v in d.items()})
        )
        return success(_u(updated))

    @extend_schema(responses={204: None}, summary="Supprimer mon compte", tags=["Users"])
    def delete(self, request):
        user = get_current_user(request)
        get_delete_user_uc().execute(DeleteUserInput(user_id=user.id))
        return no_content()
    
class UserListView(APIView):
    """GET /users/ — admin seulement"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserResponseSerializer(many=True)},
        summary="Lister tous les utilisateurs (admin)",
        tags=["Users"],
    )
    def get(self, request):
        user = get_current_user(request)
        if not user.is_admin:
            raise AuthorizationError("Droits administrateur requis.")
        users = get_list_users_uc().execute()
        return success_list(UserResponseSerializer(users, many=True).data)


class UserDetailView(APIView):
    """GET /users/{id}/ — admin seulement"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserResponseSerializer},
        summary="Détail d'un utilisateur (admin)",
        tags=["Users"],
    )
    def get(self, request, user_id: str):
        requester = get_current_user(request)
        if not requester.is_admin:
            raise AuthorizationError("Droits administrateur requis.")
        target = get_user_uc().execute(GetUserInput(user_id=user_id))
        return success(_u(target))

class UserListView(APIView):
    """GET /users/ — liste de tous les utilisateurs (admin seulement)"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserResponseSerializer(many=True)},
        summary="Lister tous les utilisateurs",
        tags=["Users"],
    )
    def get(self, request):
        user = get_current_user(request)
        if not user.is_admin:
            raise AuthorizationError("Droits administrateur requis.")
        users = get_list_users_uc().execute()
        return success_list(UserResponseSerializer(users, many=True).data)


class UserDetailAdminView(APIView):
    """GET /users/{id}/ — détail d'un utilisateur (admin seulement)"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserResponseSerializer},
        summary="Détail d'un utilisateur",
        tags=["Users"],
    )
    def get(self, request, user_id: str):
        requester = get_current_user(request)
        if not requester.is_admin:
            raise AuthorizationError("Droits administrateur requis.")
        target = get_user_uc().execute(GetUserInput(user_id=user_id))
        return success(_u(target))

urlpatterns = [
    path("me/", MeView.as_view(), name="user-me"),
    path("",            UserListView.as_view(),   name="user-list"),
    path("<str:user_id>/", UserDetailView.as_view(), name="user-detail"),
    path("<str:user_id>/", UserDetailAdminView.as_view(), name="user-detail-admin"),

]
