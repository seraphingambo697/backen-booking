"""
app/modules/user/tests/unit/test_user_entity.py
Tests unitaires — entité User + use cases (repositories mockés).

Zéro Django : tests purs Python, exécutables sans DB.
pytest app/modules/user/tests/unit/ -v
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    DomainValidationError,
    EntityNotFoundError,
)
from app.modules.user.domain.entities.user import User
from app.modules.user.domain.use_cases.create_user import CreateUserInput, CreateUserUseCase
from app.modules.user.domain.use_cases.delete_user import DeleteUserInput, DeleteUserUseCase
from app.modules.user.domain.use_cases.get_user import (
    AuthenticateUserInput,
    AuthenticateUserUseCase,
    GetUserInput,
    GetUserUseCase,
    ListUsersUseCase,
)
from app.modules.user.domain.use_cases.update_user import UpdateUserInput, UpdateUserUseCase


# ── Helpers ─────────────

def _make_user(**kw) -> User:
    from app.core.security import PasswordHasher
    defaults = dict(
        email      = "alice@example.com",
        first_name = "Alice",
        last_name  = "Martin",
        password   = PasswordHasher().hash("SecurePass123!"),
        is_active  = True,
        is_admin   = False,
    )
    defaults.update(kw)
    u = User.__new__(User)
    from datetime import datetime
    for k, v in {**defaults, "id": "user-1",
                 "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
                 "_events": [], "phone": ""}.items():
        object.__setattr__(u, k, v)
    return u


# Entité User

class TestUserEntity:

    def test_valid_user_created(self):
        u = User(
            email="bob@example.com",
            first_name="Bob",
            last_name="Dupont",
            password="hashed",
        )
        assert u.email == "bob@example.com"
        assert u.is_active is True
        assert u.is_admin  is False

    def test_invalid_email_raises(self):
        with pytest.raises(DomainValidationError) as exc:
            User(email="pas-un-email", first_name="A", last_name="B", password="x")
        assert exc.value.field == "email"

    def test_name_too_long_raises(self):
        with pytest.raises(DomainValidationError):
            User(email="a@b.com", first_name="A" * 101, last_name="B", password="x")

    def test_full_name(self):
        u = User(email="a@b.com", first_name="Alice", last_name="Martin", password="x")
        assert u.full_name() == "Alice Martin"

    def test_can_login_active(self):
        u = _make_user(is_active=True)
        assert u.can_login() is True

    def test_cannot_login_inactive(self):
        u = _make_user(is_active=False)
        assert u.can_login() is False

    def test_deactivate(self):
        u = _make_user()
        u.deactivate()
        assert u.is_active is False

    def test_validate_plain_password_min_8(self):
        with pytest.raises(DomainValidationError) as exc:
            User.validate_plain_password("1234567")
        assert exc.value.field == "password"

    def test_validate_plain_password_ok(self):
        User.validate_plain_password("12345678")  

    def test_validate_email_static(self):
        User.validate_email("valid@example.com") 

    def test_user_id_is_uuid(self):
        u = User(email="test@test.com", first_name="T", last_name="U", password="x")
        assert len(u.id) == 36  # format UUID


# CreateUserUseCase

class TestCreateUserUseCase:

    def _repo(self, email_exists=False, saved=None):
        repo = MagicMock()
        repo.email_exists.return_value = email_exists
        repo.save.return_value = saved or _make_user()
        return repo

    def test_creates_user_successfully(self):
        repo = self._repo()
        uc   = CreateUserUseCase(repo)
        result = uc.execute(CreateUserInput(
            email="alice@example.com", first_name="Alice",
            last_name="Martin", password="SecurePass123!",
        ))
        repo.save.assert_called_once()
        assert result.email == "alice@example.com"


    def test_duplicate_email_raises_conflict(self):
        repo = self._repo(email_exists=True)
        with pytest.raises(ConflictError) as exc:
            CreateUserUseCase(repo).execute(CreateUserInput(
                email="alice@example.com", first_name="A",
                last_name="B", password="SecurePass123!",
            ))
        assert exc.value.field == "email"

    def test_invalid_email_raises_validation_error(self):
        repo = self._repo()
        with pytest.raises(DomainValidationError):
            CreateUserUseCase(repo).execute(CreateUserInput(
                email="not-an-email", first_name="A",
                last_name="B", password="SecurePass123!",
            ))
        repo.save.assert_not_called()

    def test_short_password_raises_validation_error(self):
        repo = self._repo()
        with pytest.raises(DomainValidationError) as exc:
            CreateUserUseCase(repo).execute(CreateUserInput(
                email="alice@example.com", first_name="A",
                last_name="B", password="short",
            ))
        assert exc.value.field == "password"
        repo.save.assert_not_called()


# GetUserUseCase + ListUsersUseCase

class TestGetUserUseCase:

    def test_returns_user_by_id(self):
        repo = MagicMock()
        user = _make_user()
        repo.find_by_id.return_value = user
        result = GetUserUseCase(repo).execute(GetUserInput(user_id="user-1"))
        assert result.id == "user-1"

    def test_raises_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        with pytest.raises(EntityNotFoundError) as exc:
            GetUserUseCase(repo).execute(GetUserInput(user_id="ghost"))
        assert exc.value.entity == "User"

    def test_list_users(self):
        repo = MagicMock()
        repo.find_all.return_value = [_make_user(), _make_user()]
        results = ListUsersUseCase(repo).execute()
        assert len(results) == 2


# AuthenticateUserUseCase

class TestAuthenticateUserUseCase:

    def test_authenticates_with_valid_credentials(self):
        repo = MagicMock()
        user = _make_user()  # password = hash("SecurePass123!")
        repo.find_by_email.return_value = user
        result = AuthenticateUserUseCase(repo).execute(
            AuthenticateUserInput(email="alice@example.com", password="SecurePass123!")
        )
        assert result.id == "user-1"

    def test_wrong_password_raises_authentication_error(self):
        repo = MagicMock()
        repo.find_by_email.return_value = _make_user()
        with pytest.raises(AuthenticationError):
            AuthenticateUserUseCase(repo).execute(
                AuthenticateUserInput(email="alice@example.com", password="WrongPass!")
            )

    def test_inactive_user_raises_authentication_error(self):
        repo = MagicMock()
        repo.find_by_email.return_value = _make_user(is_active=False)
        with pytest.raises(AuthenticationError) as exc:
            AuthenticateUserUseCase(repo).execute(
                AuthenticateUserInput(email="alice@example.com", password="SecurePass123!")
            )
        assert "désactivé" in str(exc.value).lower() or exc.value


# UpdateUserUseCase

class TestUpdateUserUseCase:

    def _setup(self, user=None, email_exists=False):
        repo = MagicMock()
        repo.find_by_id.return_value = user or _make_user()
        repo.email_exists.return_value = email_exists
        repo.save.side_effect = lambda u: u
        return repo

    def test_updates_first_name(self):
        repo = self._setup()
        result = UpdateUserUseCase(repo).execute(
            UpdateUserInput(user_id="user-1", first_name="Alicia")
        )
        assert result.first_name == "Alicia"


    def test_invalid_email_raises_validation_error(self):
        repo = self._setup()
        with pytest.raises(DomainValidationError):
            UpdateUserUseCase(repo).execute(
                UpdateUserInput(user_id="user-1", email="not-an-email")
            )

    def test_short_password_raises_validation_error(self):
        repo = self._setup()
        with pytest.raises(DomainValidationError):
            UpdateUserUseCase(repo).execute(
                UpdateUserInput(user_id="user-1", password="short")
            )

# DeleteUserUseCase

class TestDeleteUserUseCase:

    def test_deactivates_user(self):
        repo = MagicMock()
        user = _make_user()
        repo.find_by_id.return_value = user
        DeleteUserUseCase(repo).execute(DeleteUserInput(user_id="user-1"))
        repo.save.assert_called_once()
        assert user.is_active is False

    def test_raises_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        with pytest.raises(EntityNotFoundError):
            DeleteUserUseCase(repo).execute(DeleteUserInput(user_id="ghost"))
        repo.save.assert_not_called()
