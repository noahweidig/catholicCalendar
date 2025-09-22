"""Helpers for talking to the romcal JavaScript tooling."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Sequence


class RomcalRuntimeError(RuntimeError):
    """Raised when the romcal bridge script fails."""


def default_script_path() -> Path:
    """Return the default path to the romcal bridge script."""

    return Path(__file__).resolve().parent / "scripts" / "romcal_fetch.mjs"


def fetch_calendar(
    year: int,
    *,
    locale: str = "en",
    calendar: str = "general",
    include_optional: bool = True,
    script_path: str | Path | None = None,
    extra_args: Sequence[str] | None = None,
) -> List[Mapping[str, Any]]:
    """Fetch calendar data from romcal via the Node.js bridge script."""

    script = Path(script_path) if script_path else default_script_path()
    if not script.exists():  # pragma: no cover - defensive branch
        raise FileNotFoundError(f"romcal bridge script not found at {script}")

    command = [
        "node",
        str(script),
        "--year",
        str(year),
        "--locale",
        locale,
        "--calendar",
        calendar,
    ]
    if not include_optional:
        command.append("--no-optional")
    if extra_args:
        command.extend(extra_args)

    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        raise RomcalRuntimeError(process.stderr.strip() or process.stdout.strip())

    stdout = process.stdout.strip()
    if not stdout:
        return []

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive branch
        message = "romcal bridge script did not return valid JSON"
        raise RomcalRuntimeError(message) from exc

    if not isinstance(payload, list):  # pragma: no cover - defensive branch
        raise RomcalRuntimeError("romcal bridge script must output a JSON array")

    return payload
