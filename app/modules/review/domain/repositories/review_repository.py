from abc import abstractmethod
from typing import List
from app.modules.review.domain.entities.review import Review
from app.shared.domain.base_repository import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    @abstractmethod
    def find_by_hotel(self, hotel_id: str) -> List[Review]: ...
    @abstractmethod
    def find_by_user(self, user_id: str) -> List[Review]: ...
    @abstractmethod
    def exists_for_booking(self, booking_id: str) -> bool: ...
