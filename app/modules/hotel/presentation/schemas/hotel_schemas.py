"""hotel_schemas.py — Sérialiseurs DRF (request + response)."""
from rest_framework import serializers


# ── Hotel ───────────────

class HotelResponseSerializer(serializers.Serializer):
    id          = serializers.UUIDField()
    owner_id    = serializers.UUIDField(allow_null=True)
    name        = serializers.CharField()
    description = serializers.CharField()
    address     = serializers.CharField()
    city        = serializers.CharField()
    country     = serializers.CharField()
    latitude    = serializers.FloatField()
    longitude   = serializers.FloatField()
    stars       = serializers.IntegerField()
    status      = serializers.CharField()
    phone       = serializers.CharField()
    email       = serializers.EmailField(allow_blank=True)
    website     = serializers.URLField(allow_blank=True)
    amenities   = serializers.ListField(child=serializers.CharField())
    images      = serializers.ListField(child=serializers.CharField())
    is_active   = serializers.BooleanField()
    created_at  = serializers.DateTimeField()
    updated_at  = serializers.DateTimeField()


class CreateHotelRequestSerializer(serializers.Serializer):
    name        = serializers.CharField(max_length=200)
    description = serializers.CharField(allow_blank=True, default="")
    address     = serializers.CharField(max_length=300)
    city        = serializers.CharField(max_length=100)
    country     = serializers.CharField(max_length=100)
    stars       = serializers.IntegerField(min_value=1, max_value=5)
    latitude    = serializers.FloatField(default=0.0)
    longitude   = serializers.FloatField(default=0.0)
    phone       = serializers.CharField(max_length=30, required=False, default="")
    email       = serializers.EmailField(required=False, default="")
    website     = serializers.URLField(required=False, default="")
    amenities   = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    images      = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class UpdateHotelRequestSerializer(serializers.Serializer):
    name        = serializers.CharField(max_length=200,  required=False)
    description = serializers.CharField(required=False)
    address     = serializers.CharField(max_length=300,  required=False)
    city        = serializers.CharField(max_length=100,  required=False)
    country     = serializers.CharField(max_length=100,  required=False)
    stars       = serializers.IntegerField(min_value=1, max_value=5, required=False)
    phone       = serializers.CharField(max_length=30,   required=False)
    email       = serializers.EmailField(required=False)
    website     = serializers.URLField(required=False)
    amenities   = serializers.ListField(child=serializers.CharField(), required=False)
    images      = serializers.ListField(child=serializers.CharField(), required=False)


# ── Room ────────────────

class RoomResponseSerializer(serializers.Serializer):
    id              = serializers.UUIDField()
    hotel_id        = serializers.UUIDField()
    name            = serializers.CharField()
    type            = serializers.CharField()
    description     = serializers.CharField()
    price_per_night = serializers.FloatField()
    currency        = serializers.CharField()
    capacity        = serializers.IntegerField()
    size_sqm        = serializers.IntegerField()
    bed_count       = serializers.IntegerField()
    bed_type        = serializers.CharField()
    floor           = serializers.IntegerField()
    amenities       = serializers.ListField(child=serializers.CharField())
    images          = serializers.ListField(child=serializers.CharField())
    is_available    = serializers.BooleanField()
    created_at      = serializers.DateTimeField()
    updated_at      = serializers.DateTimeField()


class CreateRoomRequestSerializer(serializers.Serializer):
    name            = serializers.CharField(max_length=200)
    type            = serializers.ChoiceField(choices=["SINGLE","DOUBLE","TWIN","SUITE","DELUXE","FAMILY"])
    description     = serializers.CharField(allow_blank=True, default="")
    price_per_night = serializers.FloatField(min_value=0.01)
    capacity        = serializers.IntegerField(min_value=1, max_value=20)
    size_sqm        = serializers.IntegerField(min_value=1,  default=25)
    bed_count       = serializers.IntegerField(min_value=1,  default=1)
    bed_type        = serializers.CharField(max_length=50,   default="Double")
    floor           = serializers.IntegerField(default=0)
    amenities       = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    images          = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class UpdateRoomRequestSerializer(serializers.Serializer):
    name            = serializers.CharField(required=False)
    price_per_night = serializers.FloatField(min_value=0.01, required=False)
    description     = serializers.CharField(required=False)
    floor           = serializers.IntegerField(required=False)
    amenities       = serializers.ListField(child=serializers.CharField(), required=False)
    images          = serializers.ListField(child=serializers.CharField(), required=False)
    is_available    = serializers.BooleanField(required=False)
