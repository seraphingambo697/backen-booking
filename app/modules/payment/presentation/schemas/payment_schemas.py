"""Sérialiseurs Payment."""
from rest_framework import serializers


class PaymentResponseSerializer(serializers.Serializer):
    id             = serializers.UUIDField()
    booking_id     = serializers.UUIDField()
    user_id        = serializers.UUIDField()
    amount         = serializers.FloatField()
    currency       = serializers.CharField()
    status         = serializers.CharField()
    method         = serializers.CharField()
    gateway_ref    = serializers.CharField()
    failure_reason = serializers.CharField()
    refunded_at    = serializers.DateTimeField(allow_null=True)
    created_at     = serializers.DateTimeField()


class ProcessPaymentRequestSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()
    method     = serializers.ChoiceField(
        choices=["CARD", "PAYPAL", "BANK_TRANSFER"],
        default="CARD",
    )
