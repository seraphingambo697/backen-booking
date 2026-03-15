from dataclasses import dataclass
from app.core.exceptions import EntityNotFoundError
from app.modules.user.domain.repositories.user_repository import UserRepository
from app.shared.domain.base_use_case import BaseUseCase

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
