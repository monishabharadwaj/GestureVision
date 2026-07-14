from __future__ import annotations

"""Unit tests for the event bus."""

from gesturevision.core.events import DomainEvent, EventBus, EventType


def test_event_bus_publishes_to_subscriber() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    bus.subscribe(EventType.APP_STARTED, received.append)
    event = DomainEvent(type=EventType.APP_STARTED, payload={"phase": 0})
    bus.publish(event)

    assert len(received) == 1
    assert received[0].payload["phase"] == 0


def test_event_bus_unsubscribe() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []
    bus.subscribe(EventType.ERROR, received.append)
    bus.unsubscribe(EventType.ERROR, received.append)
    bus.publish(DomainEvent(type=EventType.ERROR, payload={}))
    assert received == []
