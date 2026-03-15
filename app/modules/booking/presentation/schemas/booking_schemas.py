"""
app/modules/booking/presentation/schemas/booking_schemas.py
Sérialiseurs DRF request/response pour le module Booking.

Convention : les SerializerMethodField lisent des @property — jamais de méthodes.
"""
from rest_framework import serializers

from app.modules.hotel.presentation.schemas.hotel_schemas import RoomResponseSerializer


# ── Request ─────────────

class CreateBookingRequestSerializer(serializers.Serializer):
    hotel_id         = serializers.UUIDField()
    room_id          = serializers.UUIDField()
    check_in         = serializers.DateField()
    check_out        = serializers.DateField()
    guest_count      = serializers.IntegerField(min_value=1, max_value=20)
    adults           = serializers.IntegerField(min_value=0, default=0, required=False)
    children         = serializers.IntegerField(min_value=0, default=0, required=False)
    special_requests = serializers.CharField(allow_blank=True, default="")

    def validate(self, data):
        if data["check_in"] >= data["check_out"]:
            raise serializers.ValidationError(
                {"check_out": "La date de départ doit être après la date d'arrivée."}
            )
        return data


class CancelBookingRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=True, default="")


class CheckAvailabilityRequestSerializer(serializers.Serializer):
    hotel_id    = serializers.UUIDField()
    check_in    = serializers.DateField()
    check_out   = serializers.DateField()
    guest_count = serializers.IntegerField(min_value=1, default=1)
    adults      = serializers.IntegerField(min_value=0, default=0, required=False)
    children    = serializers.IntegerField(min_value=0, default=0, required=False)

    def validate(self, data):
        if data["check_in"] >= data["check_out"]:
            raise serializers.ValidationError(
                {"check_out": "La date de départ doit être après la date d'arrivée."}
            )
        return data


class ListBookingsQuerySerializer(serializers.Serializer):
    """Query params pour GET /bookings/?status=CONFIRMED"""
    status = serializers.ChoiceField(
        choices=["PENDING", "CONFIRMED", "CANCELLED", "COMPLETED"],
        required=False,
        allow_null=True,
    )


# ── Response ────────────

class BookingResponseSerializer(serializers.Serializer):
    id                  = serializers.UUIDField()
    user_id             = serializers.UUIDField()
    hotel_id            = serializers.UUIDField()
    room_id             = serializers.UUIDField()

    # Depuis @property sur l'entité
    check_in            = serializers.DateField()
    check_out           = serializers.DateField()
    nights              = serializers.IntegerField()    # @property nights → int
    guest_count         = serializers.IntegerField()   # @property guest_count → int
    total_price         = serializers.FloatField()     # @property total_price → float
    currency            = serializers.CharField()      # @property currency → str

    status              = serializers.CharField()
    status_label        = serializers.SerializerMethodField()
    special_requests    = serializers.CharField()

    cancelled_at        = serializers.DateTimeField(allow_null=True)
    cancellation_reason = serializers.CharField()

    is_cancellable      = serializers.SerializerMethodField()
    is_free_cancellation = serializers.SerializerMethodField()

    created_at          = serializers.DateTimeField()
    updated_at          = serializers.DateTimeField()

    def get_status_label(self, obj) -> str:
        from app.modules.booking.domain.entities.booking import BookingStatus
        try:
            return BookingStatus(obj.status).label()
        except (ValueError, AttributeError):
            return str(obj.status)

    def get_is_cancellable(self, obj) -> bool:
        return obj.is_cancellable()

    def get_is_free_cancellation(self, obj) -> bool:
        return obj.is_free_cancellation()


class CancelBookingResponseSerializer(serializers.Serializer):
    """Réponse enrichie de l'annulation avec infos de remboursement."""
    booking         = BookingResponseSerializer()
    is_free         = serializers.BooleanField()
    refund_amount   = serializers.FloatField()
    refund_currency = serializers.CharField()


class AvailableRoomResponseSerializer(serializers.Serializer):
    """Réponse de check_availability : chambre + prix calculé."""
    room           = RoomResponseSerializer()
    nights         = serializers.IntegerField()
    total_price    = serializers.FloatField()
    currency       = serializers.CharField()
    is_free_cancel = serializers.BooleanField()
