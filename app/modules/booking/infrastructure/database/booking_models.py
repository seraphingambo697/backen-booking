"""
Modèle ORM Django pour les réservations.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from app.modules.hotel.infrastructure.database.hotel_models import HotelModel, RoomModel


class BookingModel(models.Model):

    class Meta:
        app_label = "booking_infrastructure"
        db_table  = "bookings"
        ordering  = ["-created_at"]
        indexes   = [
            models.Index(fields=["user",    "status"]),
            models.Index(fields=["hotel",   "status"]),
            models.Index(fields=["room",    "status"]),
            models.Index(fields=["check_in", "check_out"]),
        ]

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "En attente"
        CONFIRMED = "CONFIRMED", "Confirmée"
        CANCELLED = "CANCELLED", "Annulée"
        COMPLETED = "COMPLETED", "Terminée"

    id    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        db_column="user_id",
    )
    hotel = models.ForeignKey(
        HotelModel,
        on_delete=models.CASCADE,
        related_name="bookings",
        db_column="hotel_id",
    )
    room  = models.ForeignKey(
        RoomModel,
        on_delete=models.CASCADE,
        related_name="bookings",
        db_column="room_id",
    )

    check_in  = models.DateField(db_index=True)
    check_out = models.DateField(db_index=True)

    adults   = models.IntegerField(default=1)
    children = models.IntegerField(default=0)

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency    = models.CharField(max_length=3, default="EUR")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    special_requests    = models.TextField(blank=True, default="")
    cancelled_at        = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Booking {self.id} — {self.status} ({self.check_in} → {self.check_out})"
