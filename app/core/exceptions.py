"""
app/core/exceptions.py
Hiérarchie des exceptions métier LuxStay — domaine pur, zéro Django.
Le mapping DomainException → HTTP status est dans shared/presentation/middleware.py.
"""
from __future__ import annotations


# ── Base

class DomainException(Exception):
    """Racine de toutes les exceptions métier."""

    def __init__(self, message: str, code: str = "domain_error"):
        self.message = message
        self.code    = code
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# ── Accès aux données

class EntityNotFoundError(DomainException):
    """Entité introuvable → HTTP 404."""

    def __init__(self, entity: str, identifier: str):
        super().__init__(f"{entity} '{identifier}' introuvable.", "not_found")
        self.entity     = entity
        self.identifier = identifier


class ConflictError(DomainException):
    """Violation d'unicité → HTTP 409."""

    def __init__(self, field: str, value: str):
        super().__init__(f"'{value}' est déjà utilisé pour '{field}'.", "conflict")
        self.field = field
        self.value = value


# ── Validation 

class DomainValidationError(DomainException):
    """Règle métier violée → HTTP 422."""

    def __init__(self, field: str, message: str):
        super().__init__(message, "validation_error")
        self.field = field


# ── Auth 

class AuthenticationError(DomainException):
    """Identité non prouvée → HTTP 401."""

    def __init__(self, message: str = "Identifiants invalides."):
        super().__init__(message, "authentication_error")


class AuthorizationError(DomainException):
    """Action non autorisée"""

    def __init__(self, message: str = "Action non autorisée."):
        super().__init__(message, "authorization_error")


# ── Booking

class UnavailableError(DomainException):
    """Chambre/créneau non disponible → HTTP 409."""

    def __init__(self, message: str = "Non disponible pour ces dates."):
        super().__init__(message, "unavailable")


class BookingConflictError(DomainException):
    """
    Conflit de réservation — chevauchement de dates détecté.
    Plus précis que UnavailableError : porte les IDs en conflit.
    → HTTP 409.
    """

    def __init__(
        self,
        room_id:       str,
        check_in:      str,
        check_out:     str,
        conflict_ids:  list[str] | None = None,
    ):
        super().__init__(
            f"La chambre '{room_id}' est déjà réservée du {check_in} au {check_out}.",
            "booking_conflict",
        )
        self.room_id      = room_id
        self.check_in     = check_in
        self.check_out    = check_out
        self.conflict_ids = conflict_ids or []


class BookingStateError(DomainException):
    """
    Transition d'état invalide sur une réservation.
    Ex : confirmer une réservation déjà annulée → HTTP 422.
    """

    def __init__(self, current_status: str, attempted_action: str):
        super().__init__(
            f"Impossible de '{attempted_action}' une réservation en état '{current_status}'.",
            "booking_state_error",
        )
        self.current_status   = current_status
        self.attempted_action = attempted_action


# ── Paiement

class PaymentError(DomainException):
    """Échec du paiement → HTTP 402."""

    def __init__(self, message: str = "Échec du paiement.", reason: str = ""):
        super().__init__(message, "payment_error")
        self.reason = reason


class RefundError(DomainException):
    """Échec du remboursement → HTTP 402."""

    def __init__(self, message: str = "Échec du remboursement.", reason: str = ""):
        super().__init__(message, "refund_error")
        self.reason = reason
