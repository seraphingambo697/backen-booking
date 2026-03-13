from abc import abstractmethod
from typing import List, Optional

from modules.user.domain.entities.user import User
from shared.domain.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]: ...
    @abstractmethod
    def find_all(self, active_only: bool = True) -> List[User]: ...
    @abstractmethod
    def email_exists(self, email: str) -> bool: ...