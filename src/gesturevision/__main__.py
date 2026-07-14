"""Allow ``python -m gesturevision`` launches."""

from __future__ import annotations

from gesturevision.app.application import Application


def main() -> int:
    return Application().run()


if __name__ == "__main__":
    raise SystemExit(main())
