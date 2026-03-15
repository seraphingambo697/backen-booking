from dataclasses import dataclass
from typing import List
from app.core.exceptions import AuthenticationError, EntityNotFoundError
from app.core.security import PasswordHasher
from app.modules.user.domain.entities.user import User
from app.modules.user.domain.repositories.user_repository import UserRepository
from app.shared.domain.base_use_case import BaseUseCase

@dataclass
class GetUserInput:
    user_id: str

@dataclass
class AuthenticateUserInput:
    email: str
    password: str

class GetUserUseCase(BaseUseCase[GetUserInput, User]):
    def __init__(self, repository: UserRepository):
        self.repository = repository
    def execute(self, input_data: GetUserInput) -> User:
        user = self.repository.find_by_id(input_data.user_id)
        if not user:
            raise EntityNotFoundError("User", input_data.user_id)
        return user

class ListUsersUseCase(BaseUseCase[None, List[User]]):
    def __init__(self, repository: UserRepository):
        self.repository = repository
    def execute(self, input_data=None) -> List[User]:
        return self.repository.find_all()

class AuthenticateUserUseCase(BaseUseCase[AuthenticateUserInput, User]):
    def __init__(self, repository: UserRepository):
        self.repository = repository
        self.hasher = PasswordHasher()
    def execute(self, input_data: AuthenticateUserInput) -> User:
        err = AuthenticationError("Email ou mot de passe incorrect.")
        user = self.repository.find_by_email(input_data.email)
        if not user or not self.hasher.verify(input_data.password, user.password):
            raise err
        if not user.can_login():
            raise AuthenticationError("Compte désactivé.")
        return user
