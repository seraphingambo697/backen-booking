"""
app/core/__init__.py
Re-export de toutes les exceptions pour raccourcir les imports.

    from app.core import EntityNotFoundError, BookingConflictError
"""
from app.core.exceptions import (  # noqa: F401
    DomainException,
    EntityNotFoundError,
    ConflictError,
    DomainValidationError,
    AuthenticationError,
    AuthorizationError,
    UnavailableError,
    BookingConflictError,
    BookingStateError,
    PaymentError,
    RefundError,
)
