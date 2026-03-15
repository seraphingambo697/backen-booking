"""
app/shared/presentation/middleware.py
Gestionnaire d'exceptions DRF + middleware de logging des requêtes.

Mappe chaque DomainException → code HTTP approprié.
Toutes les réponses d'erreur suivent le format de shared/presentation/responses.py.
"""
from __future__ import annotations

import logging
import time

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BookingConflictError,
    BookingStateError,
    ConflictError,
    DomainException,
    DomainValidationError,
    EntityNotFoundError,
    PaymentError,
    RefundError,
    UnavailableError,
)

logger = logging.getLogger("app")


# ── Mapping exception → HTTP status ──────────────────────────────────────────
#
# Ordre important : les sous-classes doivent apparaître AVANT leur parent.
# Ex: BookingConflictError avant UnavailableError, les deux avant DomainException.

_EXCEPTION_MAP: list[tuple[type, int]] = [
    # ── 404 ────────────
    (EntityNotFoundError,   status.HTTP_404_NOT_FOUND),
    # ── 401 ────────────
    (AuthenticationError,   status.HTTP_401_UNAUTHORIZED),
    # ── 403 ────────────
    (AuthorizationError,    status.HTTP_403_FORBIDDEN),
    # ── 402 ────────────
    (PaymentError,          status.HTTP_402_PAYMENT_REQUIRED),
    (RefundError,           status.HTTP_402_PAYMENT_REQUIRED),
    # ── 409 ────────────
    (BookingConflictError,  status.HTTP_409_CONFLICT),
    (ConflictError,         status.HTTP_409_CONFLICT),
    (UnavailableError,      status.HTTP_409_CONFLICT),
    # ── 422 ────────────
    (DomainValidationError, status.HTTP_422_UNPROCESSABLE_ENTITY),
    (BookingStateError,     status.HTTP_422_UNPROCESSABLE_ENTITY),
    # ── 400 fallback ───
    (DomainException,       status.HTTP_400_BAD_REQUEST),
]


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Exception handler DRF.
    Configuré dans settings.py :
        REST_FRAMEWORK = { "EXCEPTION_HANDLER": "app.shared.presentation.middleware.custom_exception_handler" }

    Logique :
      1. Laisse DRF gérer ses propres exceptions (ValidationError, NotAuthenticated…)
      2. Mappe les DomainException → réponse JSON structurée
      3. Log CRITICAL pour les exceptions non gérées (bug)
    """
    # 1. Exceptions DRF natives (sérialiseurs, permissions…)
    response = exception_handler(exc, context)
    if response is not None:
        return response

    # 2. Exceptions domaine
    for exc_class, http_status in _EXCEPTION_MAP:
        if isinstance(exc, exc_class):
            payload = _build_error_payload(exc)
            logger.warning("[%s] %s", exc.code, exc.message)
            return Response({"success": False, "error": payload}, status=http_status)

    # 3. Exception non gérée → 500 + log critique
    logger.critical("Exception non gérée : %s", exc, exc_info=True)
    return Response(
        {"success": False, "error": {"code": "internal_error", "message": "Erreur interne du serveur."}},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _build_error_payload(exc: DomainException) -> dict:
    """Construit le dict 'error' selon le type d'exception."""
    payload: dict = {"code": exc.code, "message": exc.message}

    if isinstance(exc, DomainValidationError):
        payload["field"] = exc.field

    elif isinstance(exc, BookingConflictError):
        payload["room_id"]      = exc.room_id
        payload["check_in"]     = exc.check_in
        payload["check_out"]    = exc.check_out
        payload["conflict_ids"] = exc.conflict_ids

    elif isinstance(exc, BookingStateError):
        payload["current_status"]   = exc.current_status
        payload["attempted_action"] = exc.attempted_action

    elif isinstance(exc, ConflictError):
        payload["field"] = exc.field
        payload["value"] = exc.value

    elif isinstance(exc, EntityNotFoundError):
        payload["entity"]     = exc.entity
        payload["identifier"] = exc.identifier

    elif isinstance(exc, (PaymentError, RefundError)):
        if exc.reason:
            payload["reason"] = exc.reason

    return payload


# ── Middleware de logging ─────────────────────────────────────────────────────

class RequestLoggingMiddleware:
    """
    Logge chaque requête HTTP : méthode, path, status, durée.

    Format : [INFO] POST /api/v1/bookings/ → 201 (45.3ms)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        t0       = time.monotonic()
        response = self.get_response(request)
        ms       = (time.monotonic() - t0) * 1000
        logger.info(
            "%s %s → %s (%.1fms)",
            request.method,
            request.path,
            response.status_code,
            ms,
        )
        return response
