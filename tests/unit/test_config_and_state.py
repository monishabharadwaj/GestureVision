from __future__ import annotations

"""Unit tests for config loading and state machine."""

from gesturevision.app.state_machine import StateMachine
from gesturevision.core.events import EventBus, EventType
from gesturevision.core.types import AppMode
from gesturevision.utils.config_loader import ConfigLoader


def test_config_loader_loads_app_config() -> None:
    loader = ConfigLoader()
    app = loader.load("app")
    assert app["app"]["name"] == "GestureVision AI"
    assert "window" in app["app"]


def test_state_machine_transitions() -> None:
    bus = EventBus()
    events: list = []
    bus.subscribe(EventType.MODE_CHANGED, events.append)

    sm = StateMachine(bus)
    assert sm.mode == AppMode.LIVE
    assert sm.transition(AppMode.PAUSED) is True
    assert sm.mode == AppMode.PAUSED
    assert len(events) == 1
