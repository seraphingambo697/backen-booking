"""
Tests unitaires BaseEntity — domain events, timestamps, égalité.
"""
from __future__ import annotations

import time
from datetime import datetime

import pytest

from app.shared.domain.base_entity import BaseEntity, DomainEvent


class SampleEntity(BaseEntity):
    name: str = ""

    def rename(self, new_name: str):
        """Test que renommer met à jour le nom et génère un événement."""
        self.name = new_name
        self.touch()
        self.collect_event("EntityRenamed", {"old": self.name, "new": new_name})


class TestBaseEntity:

    def test_auto_id_generated(self):
        """Test que chaque entité a un ID unique."""
        e = SampleEntity()
        assert e.id
        assert len(e.id) == 36  

    def test_two_entities_have_different_ids(self):
        """Test que deux entités ont des IDs différents."""
        assert SampleEntity().id != SampleEntity().id


    def test_hash_by_id(self):
        """Test que l'entité est hashable par ID."""
        e = SampleEntity()
        s = {e}
        assert e in s

    def test_touch_updates_updated_at(self):
        """Test que touch met à jour updated_at."""
        e = SampleEntity()
        t0 = e.updated_at
        time.sleep(0.01)
        e.touch()
        assert e.updated_at > t0

    def test_touch_does_not_change_created_at(self):
        """Test que touch ne change pas created_at."""
        e = SampleEntity()
        ca = e.created_at
        e.touch()
        assert e.created_at == ca

