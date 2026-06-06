#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings  # noqa: E402
from utils.config_diagnostics import build_config_diagnostics, format_config_diagnostics  # noqa: E402


def main() -> int:
    print(format_config_diagnostics(build_config_diagnostics(settings)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
