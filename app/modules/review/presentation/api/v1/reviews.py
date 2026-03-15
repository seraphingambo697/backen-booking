"""Review endpoints"""
from django.urls import path
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from app.core.dependencies import get_create_review_uc, get_list_reviews_uc, get_delete_review_uc
from app.modules.review.domain.use_cases.create_review import (
    CreateReviewInput, ListReviewsInput, DeleteReviewInput,
)
from app.modules.review.presentation.schemas.review_schemas import (
    ReviewResponseSerializer, CreateReviewRequestSerializer,
)
from app.modules.user.presentation.api.dependencies import get_current_user
from app.shared.presentation.responses import created, no_content, success_list


def _r(review):
    return ReviewResponseSerializer(review).data


class ReviewListCreateView(APIView):

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    @extend_schema(
        parameters=[OpenApiParameter("hotel_id", str, required=True, description="UUID de l'hôtel")],
        responses={200: ReviewResponseSerializer(many=True)},
        summary="Avis d'un hôtel",
        tags=["Reviews"],
    )
    def get(self, request):
        hotel_id = request.query_params.get("hotel_id", "")
        reviews  = get_list_reviews_uc().execute(ListReviewsInput(hotel_id=hotel_id))
        return success_list(ReviewResponseSerializer(reviews, many=True).data)

    @extend_schema(
        request=CreateReviewRequestSerializer,
        responses={201: ReviewResponseSerializer},
        summary="Laisser un avis",
        tags=["Reviews"],
    )
    def post(self, request):
        user = get_current_user(request)
        s    = CreateReviewRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d    = s.validated_data
        review = get_create_review_uc().execute(CreateReviewInput(
            user_id=user.id,
            hotel_id=str(d["hotel_id"]),
            booking_id=str(d["booking_id"]),
            rating=d["rating"],
            title=d.get("title", ""),
            comment=d.get("comment", ""),
        ))
        return created(_r(review))


class ReviewDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={204: None}, summary="Supprimer un avis", tags=["Reviews"])
    def delete(self, request, review_id: str):
        user = get_current_user(request)
        get_delete_review_uc().execute(DeleteReviewInput(
            review_id=review_id,
            requester_id=user.id,
            is_admin=user.is_admin,
        ))
        return no_content()


urlpatterns = [
    path("",                  ReviewListCreateView.as_view(), name="review-list"),
    path("<str:review_id>/",  ReviewDeleteView.as_view(),     name="review-delete"),
]
