from dataclasses import dataclass

from core.exceptions import EntityNotFoundError
from modules.user.domain.respository.user_repository import UserRepository
from shared.application.base_use_case import BaseUseCase


@dataclass
class DeleteUserInput:
    user_id: str

class DeleteUserUseCase(BaseUseCase[DeleteUserInput, None]):
    def __init__(self, repository: UserRepository):
        self.repository = repository
    def execute(self, input_data: DeleteUserInput) -> None:
        user = self.repository.find_by_id(input_data.user_id)
        if not user:
            raise EntityNotFoundError("User", input_data.user_id)
        user.deactivate()
        self.repository.save(user)