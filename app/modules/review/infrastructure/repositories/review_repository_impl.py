from typing import List
from app.modules.review.domain.entities.review import Review
from app.modules.review.domain.repositories.review_repository import ReviewRepository
from app.modules.review.infrastructure.database.review_models import ReviewModel
from app.shared.infrastructure.database.base_repository_impl import BaseDjangoRepository


class DjangoReviewRepository(BaseDjangoRepository[Review, ReviewModel], ReviewRepository):
    model_class = ReviewModel
    entity_name = "Review"

    def find_by_hotel(self, hotel_id: str) -> List[Review]:
        return [self._to_entity(m) for m in ReviewModel.objects.filter(hotel_id=hotel_id, is_visible=True)]

    def find_by_user(self, user_id: str) -> List[Review]:
        return [self._to_entity(m) for m in ReviewModel.objects.filter(user_id=user_id)]

    def exists_for_booking(self, booking_id: str) -> bool:
        return ReviewModel.objects.filter(booking_id=booking_id).exists()

    def _to_entity(self, m: ReviewModel) -> Review:
        r = Review.__new__(Review)
        object.__setattr__(r, "id",         str(m.id))
        object.__setattr__(r, "user_id",    str(m.user_id))
        object.__setattr__(r, "hotel_id",   str(m.hotel_id))
        object.__setattr__(r, "booking_id", str(m.booking_id))
        object.__setattr__(r, "rating",     m.rating)
        object.__setattr__(r, "title",      m.title)
        object.__setattr__(r, "comment",    m.comment)
        object.__setattr__(r, "is_visible", m.is_visible)
        object.__setattr__(r, "created_at", m.created_at)
        object.__setattr__(r, "updated_at", m.updated_at)
        return r

    def _to_model_data(self, e: Review) -> dict:
        return {"user_id": e.user_id, "hotel_id": e.hotel_id, "booking_id": e.booking_id,
                "rating": e.rating, "title": e.title, "comment": e.comment, "is_visible": e.is_visible}
