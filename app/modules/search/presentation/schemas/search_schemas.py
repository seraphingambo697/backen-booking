"""Sérialiseurs Search."""
from rest_framework import serializers


class SearchRequestSerializer(serializers.Serializer):
    city        = serializers.CharField()
    check_in    = serializers.DateField()
    check_out   = serializers.DateField()
    guest_count = serializers.IntegerField(min_value=1, default=1)
    stars_min   = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    price_max   = serializers.FloatField(min_value=0, required=False, allow_null=True)
    amenities   = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )

    def validate(self, data):
        if data["check_in"] >= data["check_out"]:
            raise serializers.ValidationError(
                {"check_out": "La date de départ doit être après la date d'arrivée."}
            )
        return data
