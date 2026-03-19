"""
app/shared/domain/base_repository.py
Interface repository de base — contrat abstrait, zéro Django.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from app.shared.domain.base_entity import BaseEntity

T = TypeVar("T", bound=BaseEntity)


class BaseRepository(ABC, Generic[T]):
    """
    Interface CRUD minimale que chaque repository doit implémenter.

    Principes :
      - Méthodes en termes métier (save, find_by_id…), pas SQL
      - Les implémentations concrètes sont dans infrastructure/
    """

    # ── CRUD de base ────

    @abstractmethod
    def save(self, entity: T) -> T:
        """Crée ou met à jour une entité. Retourne l'entité persistée."""
        ...

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """Retourne l'entité ou None si introuvable."""
        ...

    @abstractmethod
    def delete(self, entity_id: str) -> None:
        """Supprime l'entité. Lève EntityNotFoundError si absente."""
        ...

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Retourne True si l'entité existe en base."""
        ...

    # ── Opérations bulk 

    def save_all(self, entities: List[T]) -> List[T]:
        """
        Sauvegarde une liste d'entités.
        Implémentation par défaut : boucle sur save().
        Les sous-classes peuvent surcharger avec bulk_update/bulk_create.
        """
        return [self.save(e) for e in entities]

    def find_all_by_ids(self, entity_ids: List[str]) -> List[T]:
        """
        Retourne les entités correspondant aux IDs donnés.
        Implémentation par défaut : boucle sur find_by_id().
        """
        results = []
        for eid in entity_ids:
            entity = self.find_by_id(eid)
            if entity is not None:
                results.append(entity)
        return results
