"""
app/modules/hotel/infrastructure/database/hotel_models.py
Modèles ORM Django — couche infra, jamais importés dans le domaine.
"""
import uuid
from django.conf import settings
from django.db import models


class HotelModel(models.Model):
    class Meta:
        app_label = "hotel_infrastructure"
        db_table  = "hotels"
        ordering  = ["-created_at"]
        indexes   = [
            models.Index(fields=["city"]),
            models.Index(fields=["status"]),
            models.Index(fields=["stars"]),
        ]

    class Status(models.TextChoices):
        ACTIVE   = "ACTIVE",   "Actif"
        INACTIVE = "INACTIVE", "Inactif"
        PENDING  = "PENDING",  "En attente"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="hotels",
        db_column="owner_id",
    )
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    address     = models.CharField(max_length=300)
    city        = models.CharField(max_length=100)
    country     = models.CharField(max_length=100)
    latitude    = models.FloatField(default=0.0)
    longitude   = models.FloatField(default=0.0)
    stars       = models.IntegerField(default=3)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    phone       = models.CharField(max_length=30, blank=True, default="")
    email       = models.EmailField(max_length=255, blank=True, default="")
    website     = models.URLField(max_length=300, blank=True, default="")
    amenities   = models.JSONField(default=list)
    images      = models.JSONField(default=list)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.stars}★)"


class RoomModel(models.Model):
    class Meta:
        app_label = "hotel_infrastructure"
        db_table  = "rooms"
        ordering  = ["price_per_night"]
        indexes   = [
            models.Index(fields=["hotel", "is_available"]),
            models.Index(fields=["type"]),
        ]

    class RoomType(models.TextChoices):
        SINGLE = "SINGLE", "Simple"
        DOUBLE = "DOUBLE", "Double"
        TWIN   = "TWIN",   "Twin"
        SUITE  = "SUITE",  "Suite"
        DELUXE = "DELUXE", "Deluxe"
        FAMILY = "FAMILY", "Familiale"

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel           = models.ForeignKey(HotelModel, on_delete=models.CASCADE, related_name="rooms")
    name            = models.CharField(max_length=200)
    type            = models.CharField(max_length=20, choices=RoomType.choices, default=RoomType.DOUBLE)
    description     = models.TextField(blank=True, default="")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    currency        = models.CharField(max_length=3, default="EUR")
    capacity        = models.IntegerField(default=2)
    size_sqm        = models.IntegerField(default=25)
    bed_count       = models.IntegerField(default=1)
    bed_type        = models.CharField(max_length=50, default="Double")
    floor           = models.IntegerField(default=0)
    amenities       = models.JSONField(default=list)
    images          = models.JSONField(default=list)
    is_available    = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hotel.name} — {self.name} ({self.type})"
