"""
Tests unitaires Review — entité + use cases.
pytest app/modules/review/tests/unit/ -v
"""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import AuthorizationError, ConflictError, EntityNotFoundError
from app.modules.booking.domain.entities.booking import BookingStatus
from app.modules.review.domain.entities.review import Review
from app.modules.review.domain.use_cases.create_review import (
    CreateReviewInput,
    CreateReviewUseCase,
    DeleteReviewInput,
    DeleteReviewUseCase,
    ListReviewsInput,
    ListReviewsUseCase,
)
from app.core.exceptions import DomainValidationError


# ── Factories 

def _review(
    user_id: str = "uid-1",
    hotel_id: str = "hid-1",
    rating: int = 4,
    is_visible: bool = True,
) -> Review:
    """Crée un Review sans passer par __init__."""
    r = Review.__new__(Review)
    for k, v in dict(
        id="rev-1", user_id=user_id, hotel_id=hotel_id,
        booking_id="bid-1", rating=rating,
        title="Excellent séjour", comment="Très belle chambre.",
        is_visible=is_visible,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        _events=[],
    ).items():
        object.__setattr__(r, k, v)
    return r


def _booking(user_id="uid-1", status=BookingStatus.COMPLETED):
    b = MagicMock()
    b.id      = "bid-1"
    b.user_id = user_id
    b.status  = status
    return b


# Review entity

class TestReviewEntity:

    def test_valid_review_created(self):
        r = Review(user_id="uid-1", hotel_id="hid-1", booking_id="bid-1", rating=5)
        assert r.rating     == 5
        assert r.is_visible is True

    def test_rating_zero_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            Review(user_id="uid-1", hotel_id="hid-1", booking_id="bid-1", rating=0)
        assert exc.value.field == "rating"

    def test_rating_six_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            Review(user_id="uid-1", hotel_id="hid-1", booking_id="bid-1", rating=6)
        assert exc.value.field == "rating"

    def test_rating_negative_raises(self):
        with pytest.raises(DomainValidationError):
            Review(user_id="uid-1", hotel_id="hid-1", booking_id="bid-1", rating=-1)

    def test_rating_1_is_valid(self):
        r = Review(user_id="uid-1", hotel_id="hid-1", booking_id="bid-1", rating=1)
        assert r.rating == 1

    def test_rating_5_is_valid(self):
        r = Review(user_id="uid-1", hotel_id="hid-1", booking_id="bid-1", rating=5)
        assert r.rating == 5

    def test_hide_sets_invisible(self):
        r = _review(is_visible=True)
        r.hide()
        assert r.is_visible is False

    def test_hide_updates_timestamp(self):
        r = _review()
        before = r.updated_at
        r.hide()
        assert r.updated_at >= before

    def test_default_visible(self):
        r = Review(user_id="uid-1", hotel_id="hid-1", booking_id="bid-1", rating=3)
        assert r.is_visible is True

    def test_validate_rating_static(self):
        Review.validate_rating(3)  # ne lève pas

    def test_validate_rating_static_raises(self):
        with pytest.raises(DomainValidationError):
            Review.validate_rating(10)


# CreateReviewUseCase

class TestCreateReviewUseCase:

    def _uc(self, booking=None, review_exists=False, hotel_exists=True):
        review_repo  = MagicMock()
        booking_repo = MagicMock()
        hotel_repo   = MagicMock()

        booking_repo.find_by_id.return_value   = booking or _booking()
        review_repo.exists_for_booking.return_value = review_exists
        review_repo.save.side_effect           = lambda r: r
        hotel_repo.find_by_id.return_value     = MagicMock() if hotel_exists else None

        return CreateReviewUseCase(review_repo, booking_repo, hotel_repo), review_repo

    def _input(self, **kw):
        defaults = dict(
            user_id="uid-1", hotel_id="hid-1", booking_id="bid-1",
            rating=4, title="Super séjour", comment="Je recommande.",
        )
        defaults.update(kw)
        return CreateReviewInput(**defaults)

    def test_creates_review_successfully(self):
        uc, repo = self._uc()
        result = uc.execute(self._input())
        assert result.rating  == 4
        assert result.user_id == "uid-1"
        repo.save.assert_called_once()

    def test_booking_not_found_raises(self):
        uc, _ = self._uc()
        uc.review_repo  # accès normal
        # Override le booking_repo
        review_repo  = MagicMock()
        booking_repo = MagicMock()
        hotel_repo   = MagicMock()
        booking_repo.find_by_id.return_value = None
        review_repo.exists_for_booking.return_value = False
        uc2 = CreateReviewUseCase(review_repo, booking_repo, hotel_repo)
        with pytest.raises(EntityNotFoundError) as exc:
            uc2.execute(self._input())
        assert exc.value.entity == "Booking"

    def test_other_user_cannot_review(self):
        """Un utilisateur ne peut pas laisser un avis sur la réservation d'un autre."""
        booking = _booking(user_id="uid-owner")
        uc, _ = self._uc(booking=booking)
        with pytest.raises(AuthorizationError):
            uc.execute(self._input(user_id="uid-stranger"))

    def test_non_completed_booking_raises(self):
        """Impossible de laisser un avis avant la fin du séjour."""
        for status in [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCELLED]:
            booking = _booking(status=status)
            uc, _ = self._uc(booking=booking)
            with pytest.raises(AuthorizationError):
                uc.execute(self._input())

    def test_only_completed_booking_allows_review(self):
        booking = _booking(status=BookingStatus.COMPLETED)
        uc, _ = self._uc(booking=booking)
        result = uc.execute(self._input())
        assert result.rating == 4

    def test_duplicate_review_raises_conflict(self):
        """Un seul avis par réservation."""
        uc, _ = self._uc(review_exists=True)
        with pytest.raises(ConflictError):
            uc.execute(self._input())

    def test_review_saved_with_correct_fields(self):
        uc, repo = self._uc()
        uc.execute(self._input(rating=5, title="Parfait", comment="Excellent."))
        saved = repo.save.call_args[0][0]
        assert saved.rating  == 5
        assert saved.title   == "Parfait"
        assert saved.comment == "Excellent."


# ListReviewsUseCase

class TestListReviewsUseCase:

    def test_returns_reviews_for_hotel(self):
        repo = MagicMock()
        repo.find_by_hotel.return_value = [_review(), _review()]
        uc = ListReviewsUseCase(repo)
        results = uc.execute(ListReviewsInput(hotel_id="hid-1"))
        assert len(results) == 2
        repo.find_by_hotel.assert_called_once_with("hid-1")

    def test_returns_empty_list_if_no_reviews(self):
        repo = MagicMock()
        repo.find_by_hotel.return_value = []
        uc = ListReviewsUseCase(repo)
        results = uc.execute(ListReviewsInput(hotel_id="hid-unknown"))
        assert results == []

    def test_delegates_to_repository(self):
        repo = MagicMock()
        repo.find_by_hotel.return_value = []
        uc = ListReviewsUseCase(repo)
        uc.execute(ListReviewsInput(hotel_id="hid-42"))
        repo.find_by_hotel.assert_called_once_with("hid-42")


# DeleteReviewUseCase

class TestDeleteReviewUseCase:

    def _uc(self, review=None):
        repo = MagicMock()
        repo.find_by_id.return_value = review or _review(user_id="uid-1")
        repo.save.side_effect = lambda r: r
        return DeleteReviewUseCase(repo), repo

    def test_owner_can_delete(self):
        uc, repo = self._uc()
        uc.execute(DeleteReviewInput(review_id="rev-1", requester_id="uid-1"))
        # hide() est appelé → is_visible = False → save appelé
        repo.save.assert_called_once()

    def test_delete_hides_review(self):
        """La suppression = soft delete (hide), pas de vraie suppression."""
        review = _review(is_visible=True)
        uc, _ = self._uc(review=review)
        uc.execute(DeleteReviewInput(review_id="rev-1", requester_id="uid-1"))
        assert review.is_visible is False

    def test_admin_can_delete_any(self):
        review = _review(user_id="uid-owner")
        uc, repo = self._uc(review=review)
        uc.execute(DeleteReviewInput(review_id="rev-1", requester_id="admin", is_admin=True))
        repo.save.assert_called_once()

    def test_stranger_cannot_delete(self):
        review = _review(user_id="uid-owner")
        uc, _ = self._uc(review=review)
        with pytest.raises(AuthorizationError):
            uc.execute(DeleteReviewInput(review_id="rev-1", requester_id="stranger"))

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        uc = DeleteReviewUseCase(repo)
        with pytest.raises(EntityNotFoundError) as exc:
            uc.execute(DeleteReviewInput(review_id="ghost", requester_id="uid-1"))
        assert exc.value.entity == "Review"

    def test_delete_does_not_remove_from_db(self):
        uc, repo = self._uc()
        uc.execute(DeleteReviewInput(review_id="rev-1", requester_id="uid-1"))
        assert not hasattr(repo, "delete") or not repo.delete.called