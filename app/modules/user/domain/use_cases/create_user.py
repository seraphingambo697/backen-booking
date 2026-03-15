from dataclasses import dataclass
from app.core.exceptions import ConflictError
from app.core.security import PasswordHasher
from app.modules.user.domain.entities.user import User
from app.modules.user.domain.repositories.user_repository import UserRepository
from app.shared.domain.base_use_case import BaseUseCase

@dataclass
class CreateUserInput:
    email:      str
    first_name: str
    last_name:  str
    password:   str
    phone:      str = ""

class CreateUserUseCase(BaseUseCase[CreateUserInput, User]):
    def __init__(self, repository: UserRepository):
        self.repository = repository
        self.hasher = PasswordHasher()

    def execute(self, input_data: CreateUserInput) -> User:
        User.validate_email(input_data.email)
        User.validate_plain_password(input_data.password)
        if self.repository.email_exists(input_data.email):
            raise ConflictError("email", input_data.email)
        user = User(
            email=input_data.email,
            first_name=input_data.first_name,
            last_name=input_data.last_name,
            phone=input_data.phone,
            password=self.hasher.hash(input_data.password),
        )
        return self.repository.save(user)
