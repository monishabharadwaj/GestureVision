# GestureVision AI — Architecture

> Living document. Phase 0 establishes the skeleton; later phases fill in pipeline modules without rewriting the core.

## Goals

- Real-time CV (30–60 FPS target) with low latency
- MediaPipe hand tracking + gesture recognition
- Pluggable classical and AI effects
- Professional PyQt6 desktop UX
- Modular, SOLID, config-driven codebase

## Layered design

```
Presentation (PyQt6)  →  Application (controller, state)  →  Domain pipeline
                                                              ↓
                         Infrastructure (camera, MediaPipe, effects, AI)
```

### Module boundaries

| Module | Responsibility | Couples to |
|--------|----------------|------------|
| `camera/` | Frame capture | `core` types only |
| `hand_tracking/` | Landmarks | `core` contracts |
| `gesture_recognition/` | Gesture events | Hand results |
| `effects/` | Frame transforms | `Effect` protocol |
| `ai/` | Model inference | `AIModel` + Effect wrapper |
| `ui/` | Rendering / controls | Events + Qt signals |
| `core/` | Shared contracts | Nothing infra-specific |

## Data flow (from Phase 1)

```
Capture Thread → RingBuffer → Process Thread
                                  ├─ HandTracker
                                  ├─ GestureRecognizer → GestureRouter
                                  ├─ EffectEngine
                                  └─ Qt signal → VideoWidget
```

## Plugin strategy

- Effects register via `effects/registry.py` (Phase 3)
- AI models implement `AIModel` and wrap as `Effect` (Phase 5)
- Gesture → action mapping lives in `config/gestures.yaml`

## Performance

- Pre-allocated ring buffer (size from `config/app.yaml`)
- Downscale for tracking; full/preview tiers for effects
- Drop stale frames; never block the Qt main thread
- Async AI worker for heavy models

## ADRs

See `docs/adr/` for architecture decision records.
