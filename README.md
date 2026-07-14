# GestureVision AI

Real-time finger-controlled computer vision system.

Index-finger and hand-gesture interaction for live webcam effects, built as a modular desktop application (Python · OpenCV · MediaPipe · PyQt6).

**Current milestone: Phase 4 — Interactive Effects**

## Status

| Phase | Focus | Status |
|-------|--------|--------|
| 0 | Project skeleton, config, logging, PyQt6 shell | Done |
| 1 | Camera + MediaPipe hands + index finger + FPS | Done |
| 2 | Gesture recognition + config mapping | Done |
| 3 | Effect engine + classical filters | Done |
| 4 | Before/after slider, brush, reveal | **Current** |
| 5+ | AI integration, polish | Planned |
| 2 | Gesture recognition + config mapping | Planned |
| 3 | Effect engine + classical filters | Planned |
| 4+ | Interactive effects, AI, polish | Planned |

## Quick start

```bash
# From the project root
python -m venv .venv

# Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application (Phase 4 — interactive effects)
python main.py
```

## Project layout

```
gesturevision-ai/
├── main.py                 # Entry point
├── config/                 # YAML configuration (no hardcoded values)
├── assets/themes/          # QSS themes
├── src/gesturevision/      # Application package
│   ├── app/                # Bootstrap & state machine
│   ├── core/               # Contracts, types, events, frame buffer
│   ├── camera/             # Phase 1
│   ├── hand_tracking/      # Phase 1
│   ├── gesture_recognition/# Phase 2
│   ├── effects/            # Phase 3+
│   ├── ai/                 # Phase 5+
│   ├── ui/                 # PyQt6 presentation
│   └── utils/              # Config & logging helpers
├── tests/
└── docs/
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full technical design: data flow, module boundaries, plugin strategy, and performance targets.

## Requirements

- Python 3.10+
- Webcam (required from Phase 1 onward)
- Windows / macOS / Linux

## License

MIT
