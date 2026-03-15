import re
from dataclasses import dataclass
from app.core.exceptions import DomainValidationError
from app.shared.domain.base_entity import BaseEntity

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

@dataclass
class User(BaseEntity):
    email:      str  = ""
    first_name: str  = ""
    last_name:  str  = ""
    phone:      str  = ""
    password:   str  = ""
    is_active:  bool = True
    is_admin:   bool = False

    def __post_init__(self):
        if self.email:    self.validate_email(self.email)
        if self.first_name: self.validate_name(self.first_name, "first_name")
        if self.last_name:  self.validate_name(self.last_name, "last_name")

    @staticmethod
    def validate_email(email: str):
        if not _EMAIL_RE.match(email):
            raise DomainValidationError("email", f"'{email}' n'est pas un email valide.")

    @staticmethod
    def validate_name(name: str, field: str):
        if not (1 <= len(name.strip()) <= 100):
            raise DomainValidationError(field, f"{field} doit contenir entre 1 et 100 caractères.")

    @staticmethod
    def validate_plain_password(pwd: str):
        if len(pwd) < 8:
            raise DomainValidationError("password", "Mot de passe : 8 caractères minimum.")

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def deactivate(self):
        self.is_active = False
        self.touch()

    def can_login(self) -> bool:
        return self.is_active
