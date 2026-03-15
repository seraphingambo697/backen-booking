"""
app/core/database.py
Utilitaires de base de données — transactions, health checks, bulk ops.

Utilisé principalement par le module booking qui nécessite des
transactions atomiques multi-entités (Booking + Payment en une seule TX).
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Callable, TypeVar

from django.db import DatabaseError, connection, transaction

logger = logging.getLogger("app")

F = TypeVar("F", bound=Callable)


# Transactions

def atomic_transaction():
    """
    Context manager pour opérations atomiques.

    Usage dans un use case :
        from app.core.database import atomic_transaction

        with atomic_transaction():
            booking = booking_repo.save(booking)
            payment = payment_repo.save(payment)
            # rollback automatique si exception levée
    """
    return transaction.atomic()


def transactional(func: F) -> F:
    """
    Décorateur — enveloppe la méthode entière dans une transaction atomique.

    Usage sur un use case :
        class CreateBookingUseCase:
            @transactional
            def execute(self, input_data):
                ...
    """
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        with transaction.atomic():
            return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


@contextmanager
def savepoint(name: str = ""):
    """
    Savepoint nommé — pour les opérations partiellement annulables
    à l'intérieur d'une transaction plus large.

    Usage :
        with atomic_transaction():
            booking_repo.save(booking)
            with savepoint("payment"):
                payment_repo.save(payment)   # annulable sans perdre le booking
    """
    sid = transaction.savepoint()
    try:
        yield sid
        transaction.savepoint_commit(sid)
    except Exception:
        transaction.savepoint_rollback(sid)
        raise


# ── Health check ────────

def check_db_connection() -> bool:
    """
    Vérifie que la base de données est accessible.
    Utilisé par /api/health/.
    """
    try:
        connection.ensure_connection()
        return True
    except DatabaseError as exc:
        logger.error(f"DB health check failed: {exc}")
        return False


def get_db_info() -> dict:
    """Retourne les métadonnées de la connexion active (pour /api/health/)."""
    try:
        return {
            "vendor":    connection.vendor,
            "name":      str(connection.settings_dict.get("NAME", "unknown")),
            "connected": True,
        }
    except Exception:
        return {"vendor": "unknown", "name": "unknown", "connected": False}
