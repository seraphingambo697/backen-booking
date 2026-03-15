"""
app/modules/booking/presentation/api/v1/bookings.py
Endpoints Booking.

GET  /bookings/availability/          → CheckAvailabilityView  (public)
GET  /bookings/                       → liste mes réservations (auth)
POST /bookings/                       → créer une réservation  (auth)
GET  /bookings/{id}/                  → détail                 (auth)
POST /bookings/{id}/cancel/           → annuler                (auth)
POST /bookings/{id}/complete/         → terminer               (admin)
"""
from django.urls import path
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.core.dependencies import (
    get_check_availability_uc,
    get_create_booking_uc,
    get_booking_uc,
    get_list_bookings_uc,
    get_cancel_booking_uc,
    get_confirm_booking_uc,
    get_complete_booking_uc,
)
from app.modules.booking.domain.use_cases.check_availability import CheckAvailabilityInput
from app.modules.booking.domain.use_cases.create_booking     import CreateBookingInput
from app.modules.booking.domain.use_cases.get_booking        import GetBookingInput, ListBookingsInput
from app.modules.booking.domain.use_cases.cancel_booking     import CancelBookingInput
from app.modules.booking.domain.use_cases.confirm_booking    import ConfirmBookingInput
from app.modules.booking.domain.use_cases.complete_booking   import CompleteBookingInput
from app.modules.booking.presentation.schemas.booking_schemas import (
    CheckAvailabilityRequestSerializer,
    AvailableRoomResponseSerializer,
    CreateBookingRequestSerializer,
    BookingResponseSerializer,
    CancelBookingRequestSerializer,
    CancelBookingResponseSerializer,
    ListBookingsQuerySerializer,
)
from app.modules.user.presentation.api.dependencies import get_current_user, require_admin
from app.shared.presentation.responses import created, success, success_list, no_content


# ═══════════════════════════════════════════════════════════════════════════════
# DISPONIBILITÉ
# ═══════════════════════════════════════════════════════════════════════════════

class CheckAvailabilityView(APIView):
    """POST — Chambres disponibles pour un hôtel + dates + voyageurs."""
    permission_classes = [AllowAny]

    @extend_schema(
        request   = CheckAvailabilityRequestSerializer,
        responses = {200: AvailableRoomResponseSerializer(many=True)},
        summary   = "Vérifier la disponibilité",
        tags      = ["Bookings"],
    )
    def post(self, request):
        s = CheckAvailabilityRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        rooms = get_check_availability_uc().execute(CheckAvailabilityInput(
            hotel_id    = str(d["hotel_id"]),
            check_in    = d["check_in"],
            check_out   = d["check_out"],
            guest_count = d["guest_count"],
            adults      = d.get("adults", 0),
            children    = d.get("children", 0),
        ))
        serialized = AvailableRoomResponseSerializer(rooms, many=True).data
        return success_list(serialized)


# ═══════════════════════════════════════════════════════════════════════════════
# LISTE + CRÉATION
# ═══════════════════════════════════════════════════════════════════════════════

class BookingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters = [
            OpenApiParameter("status", str,
                             description="Filtrer par statut : PENDING|CONFIRMED|CANCELLED|COMPLETED"),
        ],
        responses = {200: BookingResponseSerializer(many=True)},
        summary   = "Mes réservations",
        tags      = ["Bookings"],
    )
    def get(self, request):
        user = get_current_user(request)
        qs   = ListBookingsQuerySerializer(data=request.query_params)
        qs.is_valid(raise_exception=True)

        bookings = get_list_bookings_uc().execute(ListBookingsInput(
            user_id = user.id,
            status  = qs.validated_data.get("status"),
        ))
        return success_list(BookingResponseSerializer(bookings, many=True).data)

    @extend_schema(
        request   = CreateBookingRequestSerializer,
        responses = {201: BookingResponseSerializer},
        summary   = "Créer une réservation",
        tags      = ["Bookings"],
    )
    def post(self, request):
        user = get_current_user(request)
        s    = CreateBookingRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        booking = get_create_booking_uc().execute(CreateBookingInput(
            user_id          = user.id,
            hotel_id         = str(d["hotel_id"]),
            room_id          = str(d["room_id"]),
            check_in         = d["check_in"],
            check_out        = d["check_out"],
            guest_count      = d["guest_count"],
            adults           = d.get("adults", 0),
            children         = d.get("children", 0),
            special_requests = d.get("special_requests", ""),
        ))
        return created(BookingResponseSerializer(booking).data)


# ═══════════════════════════════════════════════════════════════════════════════
# DÉTAIL
# ═══════════════════════════════════════════════════════════════════════════════

class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses = {200: BookingResponseSerializer},
        summary   = "Détail d'une réservation",
        tags      = ["Bookings"],
    )
    def get(self, request, booking_id: str):
        user    = get_current_user(request)
        booking = get_booking_uc().execute(GetBookingInput(
            booking_id   = booking_id,
            requester_id = user.id,
            is_admin     = user.is_admin,
        ))
        return success(BookingResponseSerializer(booking).data)


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class BookingCancelView(APIView):
    """POST /bookings/{id}/cancel/ — Annuler une réservation."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request   = CancelBookingRequestSerializer,
        responses = {200: CancelBookingResponseSerializer},
        summary   = "Annuler une réservation",
        tags      = ["Bookings"],
    )
    def post(self, request, booking_id: str):
        user = get_current_user(request)
        s    = CancelBookingRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        result = get_cancel_booking_uc().execute(CancelBookingInput(
            booking_id   = booking_id,
            requester_id = user.id,
            reason       = s.validated_data.get("reason", ""),
            is_admin     = user.is_admin,
        ))
        return success(CancelBookingResponseSerializer(result).data)


class BookingCompleteView(APIView):
    """POST /bookings/{id}/complete/ — Marquer terminée (admin)."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses = {200: BookingResponseSerializer},
        summary   = "Terminer une réservation (admin)",
        tags      = ["Bookings"],
    )
    def post(self, request, booking_id: str):
        require_admin(request)
        booking = get_complete_booking_uc().execute(
            CompleteBookingInput(booking_id=booking_id, is_admin=True)
        )
        return success(BookingResponseSerializer(booking).data)


# ── URL patterns ────────

urlpatterns = [
    path("availability/",
         CheckAvailabilityView.as_view(),
         name="booking-availability"),

    path("",
         BookingListCreateView.as_view(),
         name="booking-list"),

    path("<str:booking_id>/",
         BookingDetailView.as_view(),
         name="booking-detail"),

    path("<str:booking_id>/cancel/",
         BookingCancelView.as_view(),
         name="booking-cancel"),

    path("<str:booking_id>/complete/",
         BookingCompleteView.as_view(),
         name="booking-complete"),
]
