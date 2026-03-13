"""
app/core/exceptions.py
Exceptions métier globales — identiques au projet FastAPI d'origine.

Hiérarchie :
    DomainException
    ├── EntityNotFoundError      → HTTP 404
    ├── DomainValidationError    → HTTP 422
    ├── AuthenticationError      → HTTP 401
    ├── AuthorizationError       → HTTP 403
    └── ConflictError            → HTTP 409

Ces exceptions sont levées dans le DOMAINE (entités, use cases).
La couche présentation les attrape via le custom_exception_handler DRF.
"""


class DomainException(Exception):
    """Base pour toutes les exceptions métier."""
    def __init__(self, message: str, code: str = "domain_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundError(DomainException):
    """Entité introuvable."""
    def __init__(self, entity: str, identifier: str):
        super().__init__(
            message=f"{entity} '{identifier}' introuvable.",
            code="not_found",
        )
        self.entity = entity
        self.identifier = identifier


class DomainValidationError(DomainException):
    """Règle de validation métier violée."""
    def __init__(self, field: str, message: str):
        super().__init__(message=message, code="validation_error")
        self.field = field


class AuthenticationError(DomainException):
    """Identifiants invalides."""
    def __init__(self, message: str = "Identifiants invalides."):
        super().__init__(message=message, code="authentication_error")


class AuthorizationError(DomainException):
    """Droits insuffisants."""
    def __init__(self, message: str = "Action non autorisée."):
        super().__init__(message=message, code="authorization_error")


class ConflictError(DomainException):
    """Conflit de données (email déjà pris, etc.)."""
    def __init__(self, field: str, value: str):
        super().__init__(
            message=f"'{value}' est déjà utilisé pour le champ '{field}'.",
            code="conflict",
        )
        self.field = field
        self.value = value




from __future__ import annotations


# ── Base ──────────────────────────────────────────────────────────────────────

class DomainException(Exception):
    """Racine de toutes les exceptions métier."""

    def __init__(self, message: str, code: str = "domain_error"):
        self.message = message
        self.code    = code
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# ── Accès aux données ─────────────────────────────────────────────────────────

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



# ── Booking ───────────────────────────────────────────────────────────────────

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


# ── Paiement ──────────────────────────────────────────────────────────────────

class PaymentError(DomainException):
    """Échec du paiement → HTTP 402."""

    def __init__(self, message: str = "Échec du paiement.", reason: str = ""):
        super().__i0rnit__(message, "payment_error")
        self.reason = reason


class RefundError(DomainException):
    """Échec du remboursement → HTTP 402."""

    def __init__(self, message: str = "Échec du remboursement.", reason: str = ""):
        super().__init__(message, "refund_error")
        self.reason = reason


