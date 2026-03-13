"""
app/shared/domain/base_use_case.py
Contrat de base pour tous les use cases LuxStay.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

I = TypeVar("I")  # Input type
O = TypeVar("O")  # Output type


class BaseUseCase(ABC, Generic[I, O]):
    """
    Contrat unique : un use case reçoit un Input, retourne un Output.

    Convention de nommage :
      - Input  : CreateBookingInput, CancelBookingInput…
      - Output : Booking, List[Booking], None…

    Règle : execute() ne lève que des DomainException ou sous-classes.
    Jamais d'exception Django/DRF dans le domaine.
    """

    @abstractmethod
    def execute(self, input_data: I) -> O:
        """Point d'entrée du use case."""
        ...


class NoInputUseCase(ABC, Generic[O]):
    """Use case sans input — ex: ListAllHotelsUseCase."""

    @abstractmethod
    def execute(self) -> O: ...
