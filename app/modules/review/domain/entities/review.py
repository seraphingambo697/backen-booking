"""app/modules/review/domain/entities/review.py"""
from dataclasses import dataclass
from app.core.exceptions import DomainValidationError
from app.shared.domain.base_entity import BaseEntity


@dataclass
class Review(BaseEntity):
    user_id:    str   = ""
    hotel_id:   str   = ""
    booking_id: str   = ""
    rating:     int   = 5          # 1-5
    title:      str   = ""
    comment:    str   = ""
    is_visible: bool  = True

    def __post_init__(self):
        if self.rating: self.validate_rating(self.rating)

    @staticmethod
    def validate_rating(rating: int):
        if rating not in range(1, 6):
            raise DomainValidationError("rating", "La note doit être entre 1 et 5.")

    def hide(self):
        self.is_visible = False
        self.touch()
