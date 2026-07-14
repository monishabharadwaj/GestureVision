from __future__ import annotations

"""Pipeline lifecycle: camera capture, processing thread, gestures, and Qt signals."""

import logging
import threading
import time
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage

from gesturevision.accessibility.app_launcher import launch_app, launch_url
from gesturevision.accessibility.conversation_manager import ConversationManager, ConversationMode
from gesturevision.accessibility.gesture_menu import GestureMenuController
from gesturevision.accessibility.next_step_guide import GuideState, next_step_message
from gesturevision.accessibility.profile_config import ProfileSettings
from gesturevision.accessibility.touch_navigation import TouchNavigator, zones_from_app_ids
from gesturevision.camera.capture import CameraCapture
from gesturevision.camera.capture_thread import CaptureThread
from gesturevision.core.events import DomainEvent, EventBus, EventType
from gesturevision.core.exceptions import CameraError, GestureVisionError
from gesturevision.core.frame_buffer import RingBuffer
from gesturevision.core.pipeline import (
    FramePipeline,
    build_finger_controller,
    build_gesture_recognizer,
)
from gesturevision.core.types import AccessibilityProfile, Frame, GestureType, PipelineMetrics, ProcessedFrame
from gesturevision.effects.engine import EffectEngine
from gesturevision.gesture_recognition.actions import ActionCommand, ActionType, CONTINUOUS_ACTIONS
from gesturevision.gesture_recognition.gesture_router import GestureRouter
from gesturevision.hand_tracking.mediapipe_tracker import MediaPipeHandTracker
from gesturevision.performance.fps_counter import FpsCounter
from gesturevision.recording.screenshot import save_screenshot
from gesturevision.utils.qt_bridge import bgr_to_qimage

logger = logging.getLogger(__name__)


class PipelineController(QObject):
    """
    Owns the camera and processing threads and emits frames to the UI.

    Signals are thread-safe for cross-thread delivery to Qt slots.
    """

    frame_ready = pyqtSignal(QImage, object)  # QImage, PipelineMetrics
    status_changed = pyqtSignal(str)
    gesture_changed = pyqtSignal(str)
    effect_switch_requested = pyqtSignal(str)
    parameter_changed = pyqtSignal(str, float)
    screenshot_captured = pyqtSignal(str)
    pause_toggle_requested = pyqtSignal()
    error_occurred = pyqtSignal(str)

    menu_changed = pyqtSignal(list, int)  # labels, active_index
    menu_closed = pyqtSignal()
    next_step_changed = pyqtSignal(str)
    touch_hover = pyqtSignal(str)
    dialogue_updated = pyqtSignal(str, str, str)  # agent_text, user_text, detail_text

    def __init__(
        self,
        configs: dict[str, dict[str, Any]],
        project_root: Path,
        event_bus: EventBus,
        profile_settings: ProfileSettings | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._configs = configs
        self._project_root = project_root
        self._event_bus = event_bus
        self._profile_settings = profile_settings or ProfileSettings(
            profile=AccessibilityProfile.STANDARD,
        )

        perf_cfg = configs["app"].get("performance", {})
        self._buffer_size = int(perf_cfg.get("ring_buffer_size", 3))
        screenshots_rel = configs["app"].get("paths", {}).get("screenshots", "screenshots")
        self._screenshots_dir = project_root / screenshots_rel

        self._camera = CameraCapture(configs["camera"])
        self._buffer: RingBuffer[Frame] = RingBuffer(self._buffer_size)
        self._stop_event = threading.Event()
        self._capture_thread: CaptureThread | None = None
        self._process_thread: threading.Thread | None = None

        self._hand_tracker: MediaPipeHandTracker | None = None
        self._pipeline: FramePipeline | None = None
        self._gesture_router = GestureRouter(configs["gestures"])
        if self._profile_settings.gesture_mappings:
            self._gesture_router.apply_profile_mappings(self._profile_settings.gesture_mappings)
        self._effect_engine = EffectEngine(configs["effects"])
        if self._profile_settings.audio_only:
            self._effect_engine.set_active_effect("original")
        else:
            self._effect_engine.set_active_effect("original")

        a11y_root = configs.get("accessibility", {}).get("accessibility", {})
        self._menu = GestureMenuController(
            items=self._profile_settings.gesture_menu,
            apps_config=a11y_root,
        )
        apps_dict = a11y_root.get("apps", {})
        touch_ids = self._profile_settings.touch_bar or self._profile_settings.gesture_menu
        self._touch = TouchNavigator(zones=zones_from_app_ids(touch_ids, apps_dict))
        self._guide = GuideState()
        self._conversation = ConversationManager()
        self._hands_visible = False
        self._running = False
        self._latest_frame: ProcessedFrame | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def active_effect(self) -> str:
        return self._effect_engine.active_effect

    def set_active_effect(self, name: str) -> bool:
        """Switch the live effect applied to the camera feed."""
        return self._effect_engine.set_active_effect(name)

    def reset_active_effect(self) -> None:
        """Clear state on the active interactive effect."""
        self._effect_engine.reset_active_effect()

    def adjust_effect_parameter(self, target: str, value: float) -> None:
        """Adjust a runtime parameter on the active effect."""
        key = target.split(".")[-1] if "." in target else target
        self._effect_engine.adjust_active_parameter(key, value)

    def set_brush_type(self, brush_type: str) -> None:
        self._effect_engine.set_brush_type(brush_type)

    def set_brush_color(self, b: int, g: int, r: int) -> None:
        self._effect_engine.set_brush_color((b, g, r))

    def set_reveal_overlay(self, effect_name: str) -> None:
        self._effect_engine.set_reveal_overlay(effect_name)

    def conversation_active(self) -> bool:
        return self._conversation.is_active()

    def handle_conversation_utterance(self, text: str) -> None:
        """Process free-form speech during an active dialogue."""
        if not text.strip():
            return

        self.dialogue_updated.emit(self._conversation.last_agent_prompt, text, "")
        result = self._conversation.handle_utterance(text)
        self._conversation.mode = result.mode
        if result.mode != ConversationMode.IDLE and result.reply and not result.open_url:
            self._conversation.last_agent_prompt = result.reply

        spoken = result.visual_detail.strip() if result.visual_detail.strip() else result.reply
        self._announce_dialogue(result.reply, text, detail=result.visual_detail, spoken=spoken)
        if result.open_url:
            launch_url(result.open_url)
        if result.visual_detail:
            self._guide.conversation_hint = (
                "READ the lesson on screen — Peace sign to learn again, Rock for music"
            )
        elif result.direct_play:
            self._guide.conversation_hint = "Song should be playing — Rock sign for another song"
        else:
            self._guide.conversation_hint = ""
        self._update_next_step()

    def _announce_dialogue(
        self,
        agent_text: str,
        user_text: str = "",
        *,
        detail: str = "",
        spoken: str | None = None,
    ) -> None:
        self.dialogue_updated.emit(agent_text, user_text, detail)
        message = spoken if spoken else agent_text
        self.status_changed.emit(message)
        self._event_bus.publish(
            DomainEvent(
                type=EventType.ACTION_TRIGGERED,
                payload={
                    "action": "conversation",
                    "gesture": "voice",
                    "target": agent_text,
                    "label": agent_text,
                },
            )
        )

    def _start_music_chat(self) -> str:
        return self._conversation.start_music()

    def _start_learn_chat(self) -> str:
        return self._conversation.start_learn()

    def _start_free_chat(self) -> str:
        return self._conversation.start_free()

    def handle_voice_command(self, command_id: str, spoken_text: str = "") -> None:
        """Execute a spoken command — or continue a live conversation."""
        if self._conversation.is_active() and spoken_text:
            self.handle_conversation_utterance(spoken_text)
            return
        self._guide.last_voice = spoken_text
        self._update_next_step()

        if command_id == "help":
            self.status_changed.emit(
                "SAY: play music, open youtube, open chrome, edge, firefox, paint. "
                "TOUCH: point at bottom bar and hold. "
                "GESTURES: OK=menu, Peace=next, Thumbs up=open."
            )
            self._guide.last_voice = ""
            self._update_next_step()
            return

        if command_id == "learn":
            prompt = self._start_learn_chat()
            self._announce_dialogue(prompt)
            self._guide.last_voice = ""
            self._update_next_step()
            return

        if command_id == "menu":
            label = self._menu.open_menu()
            self._guide.menu_open = True
            self._guide.menu_highlight = label
            self.menu_changed.emit(self._menu.all_labels(), self._menu.index)
            self.status_changed.emit(f"Menu open — selected {label}")
            self._guide.last_voice = ""
            self._update_next_step()
            return

        if command_id == "paint":
            self._enter_brush_mode()
            self._guide.last_voice = ""
            self._update_next_step()
            return

        if command_id == "original":
            self.set_active_effect("original")
            self.effect_switch_requested.emit("original")
            self._guide.brush_mode = False
            self._guide.menu_open = False
            self.menu_closed.emit()
            self.status_changed.emit("Back to live camera view")
            self._guide.last_voice = ""
            self._update_next_step()
            return

        apps = self._profile_settings.apps.get("apps", self._profile_settings.apps)
        if command_id in apps or command_id in {"chrome", "youtube", "edge", "firefox", "music"}:
            label = self._handle_launch(command_id, self._latest_frame or self._blank_frame())
            self._guide.menu_open = False
            self.menu_closed.emit()
            self.status_changed.emit(f"Opening {label}")
            self._guide.last_voice = ""
            self._update_next_step()

    def _handle_touch(self, processed: ProcessedFrame) -> None:
        if self._profile_settings.profile != AccessibilityProfile.DANDELION:
            return
        if not self._touch.zones or processed.finger_position is None:
            self.touch_hover.emit("")
            return

        norm_x, norm_y = processed.finger_position
        pointing = processed.active_gesture == GestureType.INDEX_FINGER
        pinching = processed.active_gesture == GestureType.PINCH
        hover, tap = self._touch.update(
            norm_x,
            norm_y,
            pointing=pointing,
            pinching=pinching,
        )
        self.touch_hover.emit(hover or "")
        if tap:
            self._handle_launch(tap, processed)
            self.status_changed.emit(f"Touched {tap}")
            self._update_next_step()

    def _blank_frame(self) -> ProcessedFrame:
        import numpy as np

        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        return ProcessedFrame(
            image=blank,
            metrics=PipelineMetrics(),
            hands=[],
            finger_position=None,
            active_gesture=GestureType.UNKNOWN,
        )

    def _enter_brush_mode(self) -> None:
        self.set_active_effect("brush")
        self.effect_switch_requested.emit("brush")
        self._guide.brush_mode = True
        self._guide.menu_open = False
        self.menu_closed.emit()
        self.status_changed.emit("Paint mode — point with index finger")

    def _update_next_step(self) -> None:
        self._guide.brush_mode = self.active_effect == "brush"
        message = next_step_message(self._guide)
        self.next_step_changed.emit(message)

    def start(self) -> None:
        """Open the camera and begin capture + processing."""
        if self._running:
            return

        try:
            models_dir = self._project_root / self._configs["app"]["paths"]["models"]
            self._hand_tracker = MediaPipeHandTracker(
                config=self._configs["gestures"],
                models_dir=models_dir,
            )
            finger_controller = build_finger_controller(
                self._configs["gestures"],
                mirror_preview=bool(self._configs["app"].get("mirror_preview", True)),
            )
            gesture_recognizer = build_gesture_recognizer(self._configs["gestures"])
            if self._profile_settings.gesture_mappings:
                gesture_recognizer.apply_profile_debounce(self._profile_settings.gesture_mappings)
            self._pipeline = FramePipeline(
                hand_tracker=self._hand_tracker,
                finger_controller=finger_controller,
                gesture_recognizer=gesture_recognizer,
                effect_engine=self._effect_engine,
                mirror_preview=bool(self._configs["app"].get("mirror_preview", True)),
                fps_counter=FpsCounter(),
            )

            self._camera.start()
            self._stop_event.clear()
            self._buffer.clear()

            self._capture_thread = CaptureThread(
                camera=self._camera,
                buffer=self._buffer,
                stop_event=self._stop_event,
            )
            self._capture_thread.start()

            self._process_thread = threading.Thread(
                target=self._process_loop,
                name="ProcessThread",
                daemon=True,
            )
            self._process_thread.start()

            self._running = True
            self._guide.camera_running = True
            self._guide.menu_open = False
            self._guide.brush_mode = False
            self._guide.last_voice = ""
            self._update_next_step()
            self.status_changed.emit("Camera live — use gestures to control the app")
            self._event_bus.publish(
                DomainEvent(
                    type=EventType.CAMERA_STATUS,
                    payload={"status": "running"},
                )
            )
            logger.info("Pipeline started (Phase 4 interactive effects enabled)")
        except (CameraError, GestureVisionError) as exc:
            self._cleanup()
            message = str(exc)
            self.error_occurred.emit(message)
            self._event_bus.publish(
                DomainEvent(type=EventType.ERROR, payload={"message": message})
            )
            raise

    def stop(self) -> None:
        """Stop capture and processing threads."""
        if not self._running and not self._camera.is_open:
            return

        self._stop_event.set()
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=2.0)
            self._capture_thread = None
        if self._process_thread is not None:
            self._process_thread.join(timeout=2.0)
            self._process_thread = None

        self._effect_engine.reset_active_effect()
        self._camera.stop()
        if self._hand_tracker is not None:
            self._hand_tracker.close()
            self._hand_tracker = None
        self._pipeline = None
        self._hands_visible = False
        self._running = False
        self._latest_frame = None
        self._guide.camera_running = False
        self._guide.menu_open = False
        self._update_next_step()
        self._buffer.clear()

        self.status_changed.emit("Camera stopped")
        self.gesture_changed.emit("—")
        self._event_bus.publish(
            DomainEvent(
                type=EventType.CAMERA_STATUS,
                payload={"status": "stopped"},
            )
        )
        logger.info("Pipeline stopped")

    def _process_loop(self) -> None:
        assert self._pipeline is not None
        logger.info("Process thread started")

        while not self._stop_event.is_set():
            frame = self._buffer.latest()
            if frame is None:
                time.sleep(0.001)
                continue

            processed = self._pipeline.process(frame)
            if processed is None:
                continue

            self._latest_frame = processed
            self._publish_hand_events(processed)
            self._handle_touch(processed)
            self._handle_gestures(processed)
            self._emit_frame(processed)

        logger.info("Process thread stopped")

    def _handle_gestures(self, processed: ProcessedFrame) -> None:
        hand = processed.hands[0].handedness if processed.hands else "Right"

        if processed.action_event is not None:
            command = self._gesture_router.route(
                processed.action_event,
                pinch_strength=processed.pinch_strength,
            )
            if command is not None:
                self._execute_action(command, processed)

        if processed.active_gesture in (GestureType.INDEX_FINGER, GestureType.PINCH):
            command = self._gesture_router.route_continuous(
                processed.active_gesture,
                hand,
                pinch_strength=processed.pinch_strength,
            )
            if command is not None and command.action in CONTINUOUS_ACTIONS:
                self._execute_action(command, processed, continuous=True)

    def _execute_action(
        self,
        command: ActionCommand,
        processed: ProcessedFrame,
        *,
        continuous: bool = False,
    ) -> None:
        if continuous and command.action == ActionType.ADJUST_PARAMETER:
            if command.value is not None and command.target:
                self.adjust_effect_parameter(command.target, command.value)
                self.parameter_changed.emit(command.target, command.value)
            return

        extra_label: str | None = None

        if command.action == ActionType.SWITCH_EFFECT and command.target:
            self.set_active_effect(command.target)
            self.effect_switch_requested.emit(command.target)
            self.status_changed.emit(f"Gesture → switched to {command.target}")
        elif command.action == ActionType.CAPTURE_SCREENSHOT:
            path = save_screenshot(processed.image, self._screenshots_dir)
            self.screenshot_captured.emit(str(path))
            self.status_changed.emit(f"Screenshot saved: {path.name}")
            self._event_bus.publish(
                DomainEvent(
                    type=EventType.SCREENSHOT_CAPTURED,
                    payload={"path": str(path)},
                )
            )
        elif command.action == ActionType.TOGGLE_PAUSE:
            self.pause_toggle_requested.emit()
        elif command.action == ActionType.ADJUST_PARAMETER:
            if command.value is not None and command.target:
                self.adjust_effect_parameter(command.target, command.value)
                self.parameter_changed.emit(command.target, command.value)
        elif command.action == ActionType.LAUNCH_APP and command.target:
            if command.target == "music":
                extra_label = self._start_music_chat()
                self.status_changed.emit(extra_label)
            else:
                extra_label = self._handle_launch(command.target, processed)
        elif command.action == ActionType.START_MUSIC_CHAT:
            extra_label = self._start_music_chat()
            self.status_changed.emit(extra_label)
            self._guide.conversation_hint = "SPEAK A SONG NAME NOW — it will play directly"
        elif command.action == ActionType.START_LEARN_CHAT:
            extra_label = self._start_learn_chat()
            self.status_changed.emit(extra_label)
            self._guide.conversation_hint = (
                "SPEAK YOUR TOPIC NOW — e.g. planets, cooking, history"
            )
        elif command.action == ActionType.START_FREE_CHAT:
            extra_label = self._start_free_chat()
            self.status_changed.emit(extra_label)
            self._guide.conversation_hint = "SPEAK what you want — music, learn, or open an app"
        elif command.action == ActionType.OPEN_MENU:
            label = self._menu.open_menu()
            self._guide.menu_open = True
            self._guide.menu_highlight = label
            self.menu_changed.emit(self._menu.all_labels(), self._menu.index)
            self.status_changed.emit(f"Menu open — {label}")
        elif command.action == ActionType.MENU_NEXT:
            label = self._menu.next_item()
            if label:
                self._guide.menu_highlight = label
                self.menu_changed.emit(self._menu.all_labels(), self._menu.index)
                self.status_changed.emit(f"Next: {label}")
        elif command.action == ActionType.MENU_SELECT:
            if not self._menu.open:
                self.status_changed.emit("Open menu first — show OK sign (or say: open menu)")
                self._update_next_step()
                return
            selected = self._menu.select()
            if selected is not None:
                app_id, label = selected
                self._guide.menu_open = False
                self.menu_closed.emit()
                extra_label = self._handle_launch(app_id, processed, label=label)
                if app_id == "brush":
                    self._guide.brush_mode = True
        elif command.action == ActionType.CLOSE_MENU:
            self._menu.close()
            self._guide.menu_open = False
            self.menu_closed.emit()
            self.status_changed.emit("Menu closed")
        elif command.action in {ActionType.SPEAK_HELP, ActionType.SPEAK_STATUS}:
            if command.action == ActionType.SPEAK_HELP:
                extra_label = self._start_free_chat()
                self.status_changed.emit(extra_label)
            else:
                self.status_changed.emit(
                    "Camera active. Rock sign for music. Peace sign to learn. "
                    "Pinch or fist to pause. Thumbs up for photo."
                )

        if not continuous:
            payload = {
                "action": command.action.value,
                "gesture": command.gesture.value,
                "target": command.target,
                "value": command.value,
            }
            if command.action == ActionType.MENU_NEXT and self._menu.items:
                payload["label"] = self._menu.current_label()
            if extra_label:
                payload["label"] = extra_label
            if command.action in {
                ActionType.START_MUSIC_CHAT,
                ActionType.START_LEARN_CHAT,
                ActionType.START_FREE_CHAT,
                ActionType.LAUNCH_APP,
                ActionType.MENU_SELECT,
            }:
                payload["label"] = command.target or extra_label
            self._event_bus.publish(
                DomainEvent(
                    type=EventType.ACTION_TRIGGERED,
                    payload=payload,
                )
            )
            logger.info(
                "Action triggered: %s via %s",
                command.action.value,
                command.gesture.value,
            )
            self._guide.last_voice = ""
            self._update_next_step()

    def _handle_launch(
        self,
        app_id: str,
        processed: ProcessedFrame,
        *,
        label: str | None = None,
    ) -> str:
        normalized = app_id.strip().lower()
        if normalized == "brush":
            self._enter_brush_mode()
            return "Paint"

        if normalized == "music":
            prompt = self._start_music_chat()
            self.status_changed.emit(prompt)
            return "Music"

        try:
            launched = launch_app(normalized, self._profile_settings.apps)
            self.status_changed.emit(f"Opening {launched}")
            return label or launched
        except Exception as exc:
            message = f"Could not open {normalized}: {exc}"
            logger.error(message)
            self.status_changed.emit(message)
            return normalized

    def _publish_hand_events(self, processed: ProcessedFrame) -> None:
        has_hands = len(processed.hands) > 0
        if has_hands and not self._hands_visible:
            self._hands_visible = True
            self._event_bus.publish(DomainEvent(type=EventType.HAND_ACQUIRED, payload={}))
        elif not has_hands and self._hands_visible:
            self._hands_visible = False
            self._event_bus.publish(DomainEvent(type=EventType.HAND_LOST, payload={}))

        if processed.active_gesture != GestureType.UNKNOWN:
            label = processed.active_gesture.value.replace("_", " ")
            self.gesture_changed.emit(label)
            self._event_bus.publish(
                DomainEvent(
                    type=EventType.GESTURE_DETECTED,
                    payload={"gesture": processed.active_gesture.value},
                )
            )
        elif not processed.hands:
            self.gesture_changed.emit("—")

        self._event_bus.publish(
            DomainEvent(
                type=EventType.METRICS_UPDATED,
                payload={
                    "fps": processed.metrics.fps,
                    "tracking_ms": processed.metrics.tracking_ms,
                    "gesture_ms": processed.metrics.gesture_ms,
                    "effect_ms": processed.metrics.effect_ms,
                    "total_ms": processed.metrics.total_ms,
                },
            )
        )

    def _emit_frame(self, processed: ProcessedFrame) -> None:
        qimage = bgr_to_qimage(processed.image)
        self.frame_ready.emit(qimage, processed.metrics)

    def _cleanup(self) -> None:
        self._stop_event.set()
        self._camera.stop()
        if self._hand_tracker is not None:
            self._hand_tracker.close()
            self._hand_tracker = None
        self._pipeline = None
        self._running = False

    def shutdown(self) -> None:
        """Ensure all resources are released on application exit."""
        self.stop()
