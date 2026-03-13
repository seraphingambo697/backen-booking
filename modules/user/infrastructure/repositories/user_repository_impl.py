from typing import List, Optional

from modules.user.domain.entities.user import User
from modules.user.domain.respository.user_repository import UserRepository
from modules.user.infrastructure.models.user_model import UserModel
from shared.infrastructure.repositoryImp.base_repository_impl import BaseDjangoRepository


class DjangoUserRepository(BaseDjangoRepository[User, UserModel], UserRepository):
    model_class = UserModel
    entity_name = "User"

    def find_by_email(self, email: str) -> Optional[User]:
        try: return self._to_entity(UserModel.objects.get(email=email))
        except UserModel.DoesNotExist: return None

    def find_all(self, active_only: bool = True) -> List[User]:
        qs = UserModel.objects.filter(is_active=True) if active_only else UserModel.objects.all()
        return [self._to_entity(m) for m in qs.order_by("-created_at")]

    def email_exists(self, email: str) -> bool:
        return UserModel.objects.filter(email=email).exists()

    def _to_entity(self, m: UserModel) -> User:
        u = User.__new__(User)
        for attr in ("id","email","first_name","last_name","phone","password","is_active","is_admin","created_at","updated_at"):
            object.__setattr__(u, attr, str(getattr(m, attr)) if attr == "id" else getattr(m, attr))
        return u

    def _to_model_data(self, e: User) -> dict:
        return {"email": e.email, "first_name": e.first_name, "last_name": e.last_name,
                "phone": e.phone, "password": e.password, "is_active": e.is_active, "is_admin": e.is_admin}