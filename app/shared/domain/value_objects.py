"""
app/shared/domain/value_objects.py
Value Objects partagés — immutables, validés à la construction.

Utilisés par le module booking pour encapsuler les règles métier
sur les dates, les prix et les voyageurs.

Règle : aucun import Django ici — domaine pur.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from app.core.exceptions import DomainValidationError


# ── DateRange ───────────

@dataclass(frozen=True)
class DateRange:
    """
    Plage de dates check_in / check_out pour une réservation.
    Immutable — toute modification crée un nouvel objet.

    Invariants :
      - check_in < check_out
      - check_in >= aujourd'hui
      - durée <= max_nights (configurable)
    """
    check_in:  date
    check_out: date

    def __post_init__(self):
        if not isinstance(self.check_in, date) or not isinstance(self.check_out, date):
            raise DomainValidationError("dates", "check_in et check_out doivent être des dates.")
        if self.check_in >= self.check_out:
            raise DomainValidationError(
                "check_out",
                "La date de départ doit être strictement après la date d'arrivée.",
            )
        if self.check_in < date.today():
            raise DomainValidationError(
                "check_in",
                "La date d'arrivée ne peut pas être dans le passé.",
            )

    # ── Propriétés ──────

    @property
    def nights(self) -> int:
        """Nombre de nuits de séjour."""
        return (self.check_out - self.check_in).days

    @property
    def days(self) -> int:
        """Alias de nights pour la lisibilité."""
        return self.nights

    # ── Méthodes ────────

    def overlaps(self, other: "DateRange") -> bool:
        """
        Éviter les doubles réservations en vérifiant si les plages se chevauchent.
        Deux réservations se chevauchent si :
            mon check_in < leur check_out  ET  mon check_out > leur check_in
        """
        return self.check_in < other.check_out and self.check_out > other.check_in

    def contains(self, d: date) -> bool:
        """Retourne True si la date est dans la plage [check_in, check_out[."""
        return self.check_in <= d < self.check_out

    def hours_until_checkin(self) -> float:
        """Nombre d'heures entre maintenant et le check_in. permet d'annuler la réservation."""

        from datetime import datetime
        delta = datetime.combine(self.check_in, datetime.min.time()) - datetime.utcnow()
        return delta.total_seconds() / 3600

    def is_free_cancellation(self, min_hours: int = 48) -> bool:
        """Annulation gratuite si check_in dans plus de min_hours heures."""
        return self.hours_until_checkin() > min_hours

    def validate_max_nights(self, max_nights: int):
        if self.nights > max_nights:
            raise DomainValidationError(
                "check_out",
                f"La durée maximale d'un séjour est de {max_nights} nuits.",
            )

    # ── Constructeurs alternatifs ──────────────────────────────────────────────

    @classmethod
    def from_strings(cls, check_in: str, check_out: str) -> "DateRange":
        """Crée un DateRange depuis des chaînes ISO 8601 (YYYY-MM-DD)."""
        try:
            ci = date.fromisoformat(check_in)
            co = date.fromisoformat(check_out)
        except ValueError as e:
            raise DomainValidationError("dates", f"Format de date invalide : {e}")
        return cls(ci, co)

    def __str__(self) -> str:
        return f"{self.check_in.isoformat()} → {self.check_out.isoformat()} ({self.nights} nuit(s))"


# ── Money ───────────────

@dataclass(frozen=True)
class Money:
    """
    Montant monétaire avec devise.
    Immutable — les opérations retournent un nouvel objet Money.

    Évite les erreurs de flottants : utilise le centième comme unité interne.
    """
    amount:   float
    currency: str = "EUR"

    def __post_init__(self):
        if self.amount < 0:
            raise DomainValidationError("amount", "Un montant ne peut pas être négatif.")
        if not self.currency or len(self.currency) != 3:
            raise DomainValidationError("currency", "La devise doit être un code ISO 4217 (3 lettres).")

    # ── Opérations ──────

    def add(self, other: "Money") -> "Money":
        """Retourne la somme de deux montants."""
        self._assert_same_currency(other)
        return Money(round(self.amount + other.amount, 2), self.currency)

    def subtract(self, other: "Money") -> "Money":
        """Retourne la différence entre deux montants."""
        self._assert_same_currency(other)
        result = round(self.amount - other.amount, 2)
        if result < 0:
            raise DomainValidationError("amount", "Le résultat d'une soustraction ne peut être négatif.")
        return Money(result, self.currency)

    def multiply(self, factor: float) -> "Money":
        if factor < 0:
            raise DomainValidationError("factor", "Le facteur multiplicateur ne peut être négatif.")
        return Money(round(self.amount * factor, 2), self.currency)

    def apply_tax(self, rate: float) -> "Money":
        """Retourne le montant avec taxe incluse. rate=0.10 → +10%."""
        if not (0 <= rate <= 1):
            raise DomainValidationError("rate", "Le taux de taxe doit être entre 0 et 1.")
        return Money(round(self.amount * (1 + rate), 2), self.currency)

    def _assert_same_currency(self, other: "Money"):
        if self.currency != other.currency:
            raise DomainValidationError(
                "currency",
                f"Devises incompatibles : {self.currency} ≠ {other.currency}.",
            )

    # ── Comparaisons ────

    def is_zero(self) -> bool:
        return self.amount == 0.0

    def is_greater_than(self, other: "Money") -> bool:
        self._assert_same_currency(other)
        return self.amount > other.amount

    # ── Constructeurs ───

    @classmethod
    def zero(cls, currency: str = "EUR") -> "Money":
        return cls(0.0, currency)

    @classmethod
    def from_price_per_night(cls, price_per_night: float, nights: int, currency: str = "EUR") -> "Money":
        """Calcule le total d'un séjour : prix/nuit × nuits."""
        return cls(round(price_per_night * nights, 2), currency)

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"


# ── GuestCount ──────────

@dataclass(frozen=True)
class GuestCount:
    """
    Nombre de voyageurs avec décomposition adultes/enfants.
    Immutable.
    """
    adults:   int
    children: int = 0

    def __post_init__(self):
        if self.adults < 1:
            raise DomainValidationError("adults", "Il faut au moins 1 adulte.")
        if self.children < 0:
            raise DomainValidationError("children", "Le nombre d'enfants ne peut être négatif.")
        if self.total > 20:
            raise DomainValidationError("guests", "Le nombre maximum de voyageurs est 20.")

    @property
    def total(self) -> int:
        return self.adults + self.children

    def fits_in(self, capacity: int) -> bool:
        """Retourne True si ce groupe tient dans la capacité donnée."""
        return self.total <= capacity

    @classmethod
    def simple(cls, count: int) -> "GuestCount":
        """Crée un GuestCount avec uniquement des adultes."""
        return cls(adults=count)

    def __str__(self) -> str:
        parts = [f"{self.adults} adulte(s)"]
        if self.children:
            parts.append(f"{self.children} enfant(s)")
        return ", ".join(parts)
