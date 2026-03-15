"""Search endpoint — recherche d'hôtels disponibles"""
from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import serializers

from app.core.dependencies import get_search_hotels_uc
from app.modules.hotel.presentation.schemas.hotel_schemas import HotelResponseSerializer, RoomResponseSerializer
from app.modules.search.domain.use_cases.search_hotels import SearchHotelsInput
from app.modules.search.presentation.schemas.search_schemas import SearchRequestSerializer
from app.shared.presentation.responses import success_list


class SearchResultSerializer(serializers.Serializer):
    hotel           = HotelResponseSerializer()
    available_rooms = RoomResponseSerializer(many=True)
    min_price       = serializers.FloatField()
    nights          = serializers.SerializerMethodField()

    def get_nights(self, obj):
        ci = self.context.get("check_in")
        co = self.context.get("check_out")
        return (co - ci).days if ci and co else 0


class SearchView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SearchRequestSerializer,
        summary="Rechercher des hôtels disponibles",
        description=(
            "Retourne les hôtels avec des chambres disponibles "
            "pour les dates et critères donnés. "
            "Trié par prix croissant."
        ),
        tags=["Search"],
    )
    def post(self, request):
        s = SearchRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        results = get_search_hotels_uc().execute(SearchHotelsInput(
            city        = d["city"],
            check_in    = d["check_in"],
            check_out   = d["check_out"],
            guest_count = d["guest_count"],
            stars_min   = d.get("stars_min"),
            price_max   = d.get("price_max"),
            amenities   = d.get("amenities") or None,
        ))

        ctx  = {"check_in": d["check_in"], "check_out": d["check_out"]}
        data = SearchResultSerializer(results, many=True, context=ctx).data
        return success_list(list(data), count=len(data))


urlpatterns = [
    path("", SearchView.as_view(), name="search-hotels"),
]
