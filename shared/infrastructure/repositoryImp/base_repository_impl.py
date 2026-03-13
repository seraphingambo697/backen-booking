"""
app/shared/infrastructure/database/base_repository_impl.py
Implémentation Django de BaseRepository — CRUD + bulk ops.

Chaque repository concret hérite de cette classe et implémente :
  - _to_entity(model)    : ORM Model → entité domaine
  - _to_model_data(entity) : entité domaine → dict pour update_or_create
"""
from __future__ import annotations

import logging
from typing import Generic, List, Optional, Type, TypeVar

from django.db import models

from shared.domain.base_entity import BaseEntity
from shared.domain.base_repository import BaseRepository

EntityT = TypeVar("EntityT", bound=BaseEntity)
ModelT  = TypeVar("ModelT",  bound=models.Model)

logger = logging.getLogger("app")


class BaseDjangoRepository(BaseRepository[EntityT], Generic[EntityT, ModelT]):
    """
    Implémentation générique Django de BaseRepository.

    Utilise update_or_create(id=entity.id) pour le save()
    → un seul appel gère création et mise à jour.
    """

    model_class: Type[ModelT]
    entity_name: str = "Entity"

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def save(self, entity: EntityT) -> EntityT:
        data = self._to_model_data(entity)
        obj, created = self.model_class.objects.update_or_create(
            id=entity.id, defaults=data
        )
        logger.debug(
            "%s %s %s.",
            self.entity_name,
            entity.id,
            "créée" if created else "mise à jour",
        )
        return self._to_entity(obj)

    def find_by_id(self, entity_id: str) -> Optional[EntityT]:
        try:
            return self._to_entity(self.model_class.objects.get(id=entity_id))
        except self.model_class.DoesNotExist:
            return None

    def delete(self, entity_id: str) -> None:
        count, _ = self.model_class.objects.filter(id=entity_id).delete()
        if count == 0:
            raise EntityNotFoundError(self.entity_name, entity_id)

    def exists(self, entity_id: str) -> bool:
        return self.model_class.objects.filter(id=entity_id).exists()

    # ── Bulk ──────────────────────────────────────────────────────────────────

    def save_all(self, entities: List[EntityT]) -> List[EntityT]:
        """
        Sauvegarde une liste d'entités en N appels update_or_create.
        Pour des volumes importants, surcharger avec bulk_create/bulk_update.
        """
        return [self.save(e) for e in entities]

    def find_all_by_ids(self, entity_ids: List[str]) -> List[EntityT]:
        """Récupère plusieurs entités par leurs IDs en une seule requête SQL."""
        qs = self.model_class.objects.filter(id__in=entity_ids)
        return [self._to_entity(m) for m in qs]

    # ── À implémenter dans chaque repository concret ──────────────────────────

    def _to_entity(self, m: ModelT) -> EntityT:
        """Convertit un Model ORM en entité domaine."""
        raise NotImplementedError(
            f"{self.__class__.__name__} doit implémenter _to_entity()."
        )

    def _to_model_data(self, e: EntityT) -> dict:
        """Convertit une entité domaine en dict pour update_or_create(defaults=...)."""
        raise NotImplementedError(
            f"{self.__class__.__name__} doit implémenter _to_model_data()."
        )
