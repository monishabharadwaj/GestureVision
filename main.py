#!/usr/bin/env python3
"""Entry point for GestureVision AI."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without an editable install by adding src/ to sys.path.
_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from gesturevision.app.application import Application  # noqa: E402


def main() -> int:
    """Launch the GestureVision desktop application."""
    app = Application()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
