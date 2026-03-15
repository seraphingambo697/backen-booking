"""app/core/dependencies/user.py — Factories use cases User."""
from app.modules.user.infrastructure.repositories.user_repository_impl import DjangoUserRepository
from app.modules.user.domain.use_cases.create_user  import CreateUserUseCase
from app.modules.user.domain.use_cases.get_user     import GetUserUseCase, AuthenticateUserUseCase, ListUsersUseCase
from app.modules.user.domain.use_cases.update_user  import UpdateUserUseCase
from app.modules.user.domain.use_cases.delete_user  import DeleteUserUseCase


def get_create_user_uc()       -> CreateUserUseCase:       return CreateUserUseCase(DjangoUserRepository())
def get_authenticate_user_uc() -> AuthenticateUserUseCase: return AuthenticateUserUseCase(DjangoUserRepository())
def get_user_uc()              -> GetUserUseCase:           return GetUserUseCase(DjangoUserRepository())
def get_list_users_uc()        -> ListUsersUseCase:         return ListUsersUseCase(DjangoUserRepository())
def get_update_user_uc()       -> UpdateUserUseCase:        return UpdateUserUseCase(DjangoUserRepository())
def get_delete_user_uc()       -> DeleteUserUseCase:        return DeleteUserUseCase(DjangoUserRepository())
