"""
app/modules/hotel/presentation/api/v1/hotels.py
Endpoints Hotel & Room.

Hotels  : GET /hotels/  POST /hotels/  GET/PATCH/DELETE /hotels/{id}/
Rooms   : GET /hotels/{id}/rooms/  POST /hotels/{id}/rooms/
          GET/PATCH /hotels/{id}/rooms/{room_id}/
Status  : POST /hotels/{id}/activate|deactivate
"""
from django.urls import path
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.core.dependencies import (
    get_create_hotel_uc, get_hotel_uc, get_list_hotels_uc,
    get_update_hotel_uc, get_delete_hotel_uc,
    get_create_room_uc, get_room_uc, get_list_rooms_uc, get_update_room_uc,
)
from app.modules.hotel.domain.use_cases.create_hotel  import CreateHotelInput
from app.modules.hotel.domain.use_cases.get_hotel     import GetHotelInput, ListHotelsInput
from app.modules.hotel.domain.use_cases.update_hotel  import UpdateHotelInput
from app.modules.hotel.domain.use_cases.delete_hotel  import DeleteHotelInput
from app.modules.hotel.domain.use_cases.manage_rooms  import (
    CreateRoomInput, GetRoomInput, ListRoomsInput, UpdateRoomInput,
)
from app.modules.hotel.presentation.schemas.hotel_schemas import (
    HotelResponseSerializer, CreateHotelRequestSerializer, UpdateHotelRequestSerializer,
    RoomResponseSerializer, CreateRoomRequestSerializer, UpdateRoomRequestSerializer,
)
from app.modules.user.presentation.api.dependencies import get_current_user, require_admin


# ── Helpers ─────────────

def _hotel_response(hotel):
    return HotelResponseSerializer(hotel).data

def _room_response(room):
    return RoomResponseSerializer(room).data


# ═══════════════════════════════════════════════════════════════════════════════
# HOTELS
# ═══════════════════════════════════════════════════════════════════════════════

class HotelListCreateView(APIView):
    """GET  → liste publique des hôtels (filtrable par ville)
       POST → créer un hôtel (admin requis)"""

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    @extend_schema(
        parameters=[OpenApiParameter("city", str, description="Filtrer par ville")],
        responses={200: HotelResponseSerializer(many=True)},
        summary="Lister les hôtels",
        tags=["Hotels"],
    )
    def get(self, request):
        city = request.query_params.get("city")
        hotels = get_list_hotels_uc().execute(ListHotelsInput(city=city))
        return Response(HotelResponseSerializer(hotels, many=True).data)

    @extend_schema(
        request=CreateHotelRequestSerializer,
        responses={201: HotelResponseSerializer},
        summary="Créer un hôtel",
        tags=["Hotels"],
    )
    def post(self, request):
        user = require_admin(request)
        s = CreateHotelRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        hotel = get_create_hotel_uc().execute(CreateHotelInput(owner_id=user.id, **d))
        return Response(_hotel_response(hotel), status=status.HTTP_201_CREATED)


class HotelDetailView(APIView):
    """GET → détail public   PATCH → modifier   DELETE → désactiver"""

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    @extend_schema(
        responses={200: HotelResponseSerializer},
        summary="Détail d'un hôtel",
        tags=["Hotels"],
    )
    def get(self, request, hotel_id: str):
        hotel = get_hotel_uc().execute(GetHotelInput(hotel_id=hotel_id))
        return Response(_hotel_response(hotel))

    @extend_schema(
        request=UpdateHotelRequestSerializer,
        responses={200: HotelResponseSerializer},
        summary="Modifier un hôtel",
        tags=["Hotels"],
    )
    def patch(self, request, hotel_id: str):
        user = get_current_user(request)
        s = UpdateHotelRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        hotel = get_update_hotel_uc().execute(UpdateHotelInput(
            hotel_id=hotel_id,
            requester_id=user.id,
            is_admin=user.is_admin,
            **s.validated_data,
        ))
        return Response(_hotel_response(hotel))

    @extend_schema(
        responses={204: None},
        summary="Désactiver un hôtel (soft delete)",
        tags=["Hotels"],
    )
    def delete(self, request, hotel_id: str):
        user = get_current_user(request)
        get_delete_hotel_uc().execute(DeleteHotelInput(
            hotel_id=hotel_id,
            requester_id=user.id,
            is_admin=user.is_admin,
        ))
        return Response(status=status.HTTP_204_NO_CONTENT)


class HotelActivateView(APIView):
    """POST /hotels/{id}/activate — réactiver un hôtel (admin)."""
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: HotelResponseSerializer}, summary="Activer un hôtel", tags=["Hotels"])
    def post(self, request, hotel_id: str):
        require_admin(request)
        hotel = get_hotel_uc().execute(GetHotelInput(hotel_id=hotel_id))
        hotel.activate()
        from app.core.dependencies import get_update_hotel_uc
        # On sauvegarde via le repo directement pour le changement de status
        from app.modules.hotel.infrastructure.repositories.hotel_repository_impl import DjangoHotelRepository
        saved = DjangoHotelRepository().save(hotel)
        return Response(_hotel_response(saved))


# ═══════════════════════════════════════════════════════════════════════════════
# ROOMS
# ═══════════════════════════════════════════════════════════════════════════════

class RoomListCreateView(APIView):
    """GET  → chambres d'un hôtel (public)
       POST → créer une chambre (propriétaire)"""

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    @extend_schema(
        parameters=[OpenApiParameter("available_only", bool, description="Uniquement les chambres disponibles")],
        responses={200: RoomResponseSerializer(many=True)},
        summary="Chambres d'un hôtel",
        tags=["Rooms"],
    )
    def get(self, request, hotel_id: str):
        available_only = request.query_params.get("available_only", "false").lower() == "true"
        rooms = get_list_rooms_uc().execute(ListRoomsInput(hotel_id=hotel_id, available_only=available_only))
        return Response(RoomResponseSerializer(rooms, many=True).data)

    @extend_schema(
        request=CreateRoomRequestSerializer,
        responses={201: RoomResponseSerializer},
        summary="Créer une chambre",
        tags=["Rooms"],
    )
    def post(self, request, hotel_id: str):
        user = get_current_user(request)
        s = CreateRoomRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        room = get_create_room_uc().execute(CreateRoomInput(
            hotel_id=hotel_id,
            requester_id=user.id,
            **s.validated_data,
        ))
        return Response(_room_response(room), status=status.HTTP_201_CREATED)


class RoomDetailView(APIView):
    """GET → détail chambre (public)   PATCH → modifier (propriétaire)"""

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    @extend_schema(
        responses={200: RoomResponseSerializer},
        summary="Détail d'une chambre",
        tags=["Rooms"],
    )
    def get(self, request, hotel_id: str, room_id: str):
        room = get_room_uc().execute(GetRoomInput(room_id=room_id))
        return Response(_room_response(room))

    @extend_schema(
        request=UpdateRoomRequestSerializer,
        responses={200: RoomResponseSerializer},
        summary="Modifier une chambre",
        tags=["Rooms"],
    )
    def patch(self, request, hotel_id: str, room_id: str):
        user = get_current_user(request)
        s = UpdateRoomRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        room = get_update_room_uc().execute(UpdateRoomInput(
            room_id=room_id,
            requester_id=user.id,
            is_admin=user.is_admin,
            **s.validated_data,
        ))
        return Response(_room_response(room))


# ── URL patterns ────────

urlpatterns = [
    path("",
         HotelListCreateView.as_view(),
         name="hotel-list"),

    path("<str:hotel_id>/",
         HotelDetailView.as_view(),
         name="hotel-detail"),

    path("<str:hotel_id>/activate/",
         HotelActivateView.as_view(),
         name="hotel-activate"),

    path("<str:hotel_id>/rooms/",
         RoomListCreateView.as_view(),
         name="room-list"),

    path("<str:hotel_id>/rooms/<str:room_id>/",
         RoomDetailView.as_view(),
         name="room-detail"),
]
