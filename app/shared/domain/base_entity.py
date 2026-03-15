"""
app/shared/domain/base_entity.py
Entité de base — identité UUID, timestamps, domain events.

Les domain events permettent aux use cases de publier
des événements (BookingCreated, PaymentSucceeded…) sans
coupler le domaine à la couche infrastructure.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


# ── Domain Event 

@dataclass
class DomainEvent:
    """
    Événement immutable émis par une entité lors d'un changement d'état.

    Exemples : BookingConfirmed, PaymentSucceeded, BookingCancelled.
    Les événements sont collectés sur l'entité puis dispatchés
    par le use case après la sauvegarde.
    """
    event_type:  str
    entity_id:   str
    entity_type: str
    payload:     dict = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return f"{self.event_type}({self.entity_type}:{self.entity_id})"


# ── Base Entity 

@dataclass
class BaseEntity:
    """
    Classe de base pour toutes les entités domaine.

    Fournit :
      - id UUID auto-généré
      - timestamps created_at / updated_at
      - touch() pour mettre à jour updated_at
      - domain events : collect_event() + pull_events()
    """
    id:         str      = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Liste privée d'événements — non sérialisée, non persistée
    _events: List[DomainEvent] = field(default_factory=list, init=False, repr=False, compare=False)

    # ── Identité

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BaseEntity) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    # ── Timestamps

    def touch(self):
        """Met à jour updated_at à maintenant (UTC)."""
        self.updated_at = datetime.utcnow()

    # ── Domain Events ───

    def collect_event(self, event_type: str, payload: dict | None = None):
        """
        Enregistre un domain event sur cette entité.

        Usage dans une entité :
            def confirm(self):
                self.status = BookingStatus.CONFIRMED
                self.touch()
                self.collect_event("BookingConfirmed", {"booking_id": self.id})
        """
        event = DomainEvent(
            event_type  = event_type,
            entity_id   = self.id,
            entity_type = self.__class__.__name__,
            payload     = payload or {},
        )
        self._events.append(event)

    def pull_events(self) -> List[DomainEvent]:
        """
        Retourne et vide la liste des événements en attente.
        Appelé par le use case après repository.save().

        Pattern :
            booking = booking_repo.save(booking)
            for event in booking.pull_events():
                event_bus.publish(event)
        """
        events, self._events = self._events, []
        return events

    def has_pending_events(self) -> bool:
        return bool(self._events)
