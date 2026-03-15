"""app/core/dependencies/review.py — Factories use cases Review."""
from app.modules.review.infrastructure.repositories.review_repository_impl   import DjangoReviewRepository
from app.modules.booking.infrastructure.repositories.booking_repository_impl  import DjangoBookingRepository
from app.modules.hotel.infrastructure.repositories.hotel_repository_impl      import DjangoHotelRepository
from app.modules.review.domain.use_cases.create_review import CreateReviewUseCase
from app.modules.review.domain.use_cases.get_review    import ListReviewsUseCase
from app.modules.review.domain.use_cases.delete_review import DeleteReviewUseCase


def get_create_review_uc() -> CreateReviewUseCase:
    return CreateReviewUseCase(DjangoReviewRepository(), DjangoBookingRepository(), DjangoHotelRepository())

def get_list_reviews_uc()  -> ListReviewsUseCase:  return ListReviewsUseCase(DjangoReviewRepository())
def get_delete_review_uc() -> DeleteReviewUseCase: return DeleteReviewUseCase(DjangoReviewRepository())
