
"""
app/core/__init__.py
Re-export de toutes les exceptions pour raccourcir les imports.
"""
from core.exceptions import ( 
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
