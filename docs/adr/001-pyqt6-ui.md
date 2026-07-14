# ADR-001: PyQt6 for the desktop UI

- Status: Accepted
- Date: 2026-07-14

## Context

The product must feel like professional desktop software, not an OpenCV `imshow` demo.

## Decision

Use **PyQt6** for the presentation layer, with QSS themes and a modular widget layout.

## Consequences

- Camera / CV work must run off the Qt main thread.
- Numpy ↔ QImage bridging is required (Phase 1).
- Richer UI cost vs. Tkinter simplicity.
