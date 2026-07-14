from __future__ import annotations

"""Gesture rule protocol and registry."""

from typing import Protocol

from gesturevision.core.types import GestureType, HandResult


class GestureRule(Protocol):
    """Evaluates whether a hand pose matches a gesture."""

    gesture: GestureType

    def evaluate(self, hand: HandResult) -> float:
        """
        Return a confidence score in [0, 1].

        0.0 means no match; higher values indicate stronger matches.
        """


# Evaluation order: more specific gestures first to reduce ambiguity.
GESTURE_RULES: list[GestureRule] = []


def _register(rule: GestureRule) -> GestureRule:
    GESTURE_RULES.append(rule)
    return rule


def get_gesture_rules() -> list[GestureRule]:
    """Return gesture rules in priority order."""
    if not GESTURE_RULES:
        _load_rules()
    return list(GESTURE_RULES)


def _load_rules() -> None:
    from gesturevision.gesture_recognition.gestures import (
        closed_fist,
        index_finger,
        ok_sign,
        peace,
        pinch,
        rock_sign,
        thumbs_up,
        x_sign,
    )

    for module in (
        ok_sign,
        pinch,
        x_sign,
        peace,
        rock_sign,
        thumbs_up,
        closed_fist,
        index_finger,
    ):
        _register(module.rule)
