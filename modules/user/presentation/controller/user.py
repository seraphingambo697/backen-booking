"""User profile endpoints"""
from django.urls import path
from drf_spectacular.utils import extend_schema
from modules.user.application.use_cases.update_user import UpdateUserInput
from modules.user.presentation.controller.dependencies import get_current_user
from modules.user.presentation.schemas.user_schema import UpdateUserRequestSerializer, UserResponseSerializer
from modules.user.presentation.schemas.user_schema import UserResponseSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView



def _u(user): return UserResponseSerializer(user).data


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserResponseSerializer}, summary="Mon profil", tags=["Users"])
    def get(self, request):
        return Response(_u(get_current_user(request)))

    @extend_schema(request=UpdateUserRequestSerializer, responses={200: UserResponseSerializer},
                   summary="Modifier mon profil", tags=["Users"])
    def patch(self, request):
        user = get_current_user(request)
        s = UpdateUserRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        updated = get_update_user_uc().execute(UpdateUserInput(
            user_id=user.id, **{k: v for k, v in d.items()}
        ))
        return Response(_u(updated))

    @extend_schema(responses={204: None}, summary="Désactiver mon compte", tags=["Users"])
    def delete(self, request):
        user = get_current_user(request)
        get_delete_user_uc().execute(DeleteUserInput(user_id=user.id))
        return Response(status=status.HTTP_204_NO_CONTENT)

