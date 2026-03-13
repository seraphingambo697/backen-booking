"""
app/shared/infrastructure/database/transactional.py
Décorateur @transactional pour les use cases multi-repo.

Utilisé principalement par CreateBookingUseCase et ProcessPaymentUseCase
qui doivent persister plusieurs entités dans une seule transaction.

Usage :
    from app.shared.infrastructure.database.transactional import transactional

    class CreateBookingUseCase(BaseUseCase):

        @transactional
        def execute(self, input_data):
            booking = self.booking_repo.save(booking)
            payment = self.payment_repo.save(payment)
            return booking     # rollback automatique si exception
"""
from __future__ import annotations

import functools
import logging
from typing import Callable, TypeVar

from django.db import transaction

logger = logging.getLogger("app")

F = TypeVar("F", bound=Callable)


def transactional(method: F) -> F:
    """
    Enveloppe la méthode dans un django.db.transaction.atomic().

    - Si la méthode se termine normalement → commit.
    - Si une exception est levée (DomainException ou autre) → rollback complet.
    - Compatible avec les savepoints imbriqués.
    """

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        with transaction.atomic():
            logger.debug("TX ouverte — %s.%s", args[0].__class__.__name__, method.__name__)
            result = method(*args, **kwargs)
            logger.debug("TX committée — %s.%s", args[0].__class__.__name__, method.__name__)
            return result

    return wrapper  # type: ignore[return-value]
