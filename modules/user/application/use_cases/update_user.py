from dataclasses import dataclass
from typing import Optional

from core.exceptions import ConflictError, EntityNotFoundError
from core.security import PasswordHasher
from modules.user.domain.entities.user import User
from modules.user.domain.respository.user_repository import UserRepository
from shared.application.base_use_case import BaseUseCase

@dataclass
class UpdateUserInput:
    user_id:    str
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    phone:      Optional[str] = None
    email:      Optional[str] = None
    password:   Optional[str] = None

class UpdateUserUseCase(BaseUseCase[UpdateUserInput, User]):
    def __init__(self, repository: UserRepository):
        self.repository = repository
        self.hasher = PasswordHasher()
    def execute(self, input_data: UpdateUserInput) -> User:
        user = self.repository.find_by_id(input_data.user_id)
        if not user:
            raise EntityNotFoundError("User", input_data.user_id)
        if input_data.first_name: user.first_name = input_data.first_name
        if input_data.last_name:  user.last_name  = input_data.last_name
        if input_data.phone:      user.phone       = input_data.phone
        if input_data.email and input_data.email != user.email:
            User.validate_email(input_data.email)
            if self.repository.email_exists(input_data.email):
                raise ConflictError("email", input_data.email)
            user.email = input_data.email
        if input_data.password:
            User.validate_plain_password(input_data.password)
            user.password = self.hasher.hash(input_data.password)
        user.touch()
        return self.repository.save(user)