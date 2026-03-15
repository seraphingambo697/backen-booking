"""Review use cases"""
from dataclasses import dataclass
from typing import List

from app.core.exceptions import AuthorizationError, ConflictError, EntityNotFoundError
from app.modules.booking.domain.repositories.booking_repository import BookingRepository
from app.modules.booking.domain.entities.booking import BookingStatus
from app.modules.hotel.domain.repositories.hotel_repository import HotelRepository
from app.modules.review.domain.entities.review import Review
from app.modules.review.domain.repositories.review_repository import ReviewRepository
from app.shared.domain.base_use_case import BaseUseCase


# ── CreateReview ────────
@dataclass
class CreateReviewInput:
    user_id:    str
    hotel_id:   str
    booking_id: str
    rating:     int
    title:      str
    comment:    str

class CreateReviewUseCase(BaseUseCase[CreateReviewInput, Review]):
    def __init__(self, review_repo: ReviewRepository, booking_repo: BookingRepository, hotel_repo: HotelRepository):
        self.review_repo  = review_repo
        self.booking_repo = booking_repo
        self.hotel_repo   = hotel_repo

    def execute(self, i: CreateReviewInput) -> Review:
        # Le user doit avoir séjourné dans cet hôtel
        booking = self.booking_repo.find_by_id(i.booking_id)
        if not booking:
            raise EntityNotFoundError("Booking", i.booking_id)
        if booking.user_id != i.user_id:
            raise AuthorizationError("Cette réservation ne vous appartient pas.")
        if booking.status != BookingStatus.COMPLETED:
            raise AuthorizationError("Vous ne pouvez laisser un avis qu'après votre séjour.")
        # Pas déjà reviewé
        if self.review_repo.exists_for_booking(i.booking_id):
            raise ConflictError("booking_id", i.booking_id)

        review = Review(
            user_id=i.user_id, hotel_id=i.hotel_id, booking_id=i.booking_id,
            rating=i.rating, title=i.title, comment=i.comment,
        )
        return self.review_repo.save(review)


# ── ListReviews ─────────
@dataclass
class ListReviewsInput:
    hotel_id: str

class ListReviewsUseCase(BaseUseCase[ListReviewsInput, List[Review]]):
    def __init__(self, repository: ReviewRepository):
        self.repository = repository
    def execute(self, i: ListReviewsInput) -> List[Review]:
        return self.repository.find_by_hotel(i.hotel_id)


# ── DeleteReview ────────
@dataclass
class DeleteReviewInput:
    review_id:    str
    requester_id: str
    is_admin:     bool = False

class DeleteReviewUseCase(BaseUseCase[DeleteReviewInput, None]):
    def __init__(self, repository: ReviewRepository):
        self.repository = repository
    def execute(self, i: DeleteReviewInput) -> None:
        review = self.repository.find_by_id(i.review_id)
        if not review: raise EntityNotFoundError("Review", i.review_id)
        if review.user_id != i.requester_id and not i.is_admin:
            raise AuthorizationError("Vous ne pouvez pas supprimer cet avis.")
        review.hide()
        self.repository.save(review)
