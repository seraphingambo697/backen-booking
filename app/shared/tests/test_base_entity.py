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
        self.name = new_name
        self.touch()
        self.collect_event("EntityRenamed", {"old": self.name, "new": new_name})


class TestBaseEntity:

    def test_auto_id_generated(self):
        e = SampleEntity()
        assert e.id
        assert len(e.id) == 36  

    def test_two_entities_have_different_ids(self):
        assert SampleEntity().id != SampleEntity().id

    def test_equality_by_id(self):
        e1 = SampleEntity()
        e2 = SampleEntity()
        e2_copy = SampleEntity()
        object.__setattr__(e2_copy, "id", e1.id)
        assert e1 == e2_copy
        assert e1 != e2

    def test_hash_by_id(self):
        e = SampleEntity()
        s = {e}
        assert e in s

    def test_touch_updates_updated_at(self):
        e = SampleEntity()
        t0 = e.updated_at
        time.sleep(0.01)
        e.touch()
        assert e.updated_at > t0

    def test_touch_does_not_change_created_at(self):
        e = SampleEntity()
        ca = e.created_at
        e.touch()
        assert e.created_at == ca


class TestDomainEvents:

    def test_collect_event(self):
        e = SampleEntity()
        e.collect_event("SomethingHappened", {"key": "value"})
        assert e.has_pending_events() is True

    def test_pull_events_clears_list(self):
        e = SampleEntity()
        e.collect_event("E1")
        e.collect_event("E2")
        events = e.pull_events()
        assert len(events) == 2
        assert not e.has_pending_events()

    def test_pull_events_returns_correct_types(self):
        e = SampleEntity()
        e.collect_event("TestEvent", {"x": 1})
        events = e.pull_events()
        assert isinstance(events[0], DomainEvent)
        assert events[0].event_type  == "TestEvent"
        assert events[0].entity_id   == e.id
        assert events[0].entity_type == "SampleEntity"
        assert events[0].payload     == {"x": 1}

    def test_pull_events_twice_returns_empty(self):
        e = SampleEntity()
        e.collect_event("E1")
        e.pull_events()
        assert e.pull_events() == []

    def test_no_events_by_default(self):
        e = SampleEntity()
        assert not e.has_pending_events()
        assert e.pull_events() == []
