"""Sérialiseurs Review."""
from rest_framework import serializers


class ReviewResponseSerializer(serializers.Serializer):
    id         = serializers.UUIDField()
    user_id    = serializers.UUIDField()
    hotel_id   = serializers.UUIDField()
    booking_id = serializers.UUIDField()
    rating     = serializers.IntegerField()
    title      = serializers.CharField()
    comment    = serializers.CharField()
    is_visible = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class CreateReviewRequestSerializer(serializers.Serializer):
    hotel_id   = serializers.UUIDField()
    booking_id = serializers.UUIDField()
    rating     = serializers.IntegerField(min_value=1, max_value=5)
    title      = serializers.CharField(max_length=200, allow_blank=True, default="")
    comment    = serializers.CharField(allow_blank=True, default="")
