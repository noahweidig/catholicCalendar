"""Tests for the romcal adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from catholic_calendar import romcal_adapter


class DummyProcess:
    def __init__(self, stdout: str = '', stderr: str = '', returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_fetch_calendar_returns_json(monkeypatch, tmp_path):
    script = tmp_path / "romcal_fetch.mjs"
    script.write_text("console.log('stub');\n")

    def fake_run(command, capture_output, text, check):
        assert command[0] == "node"
        assert "--year" in command
        return DummyProcess(stdout='[{"date": "2025-01-01", "name": "Mary"}]')

    monkeypatch.setattr(romcal_adapter.subprocess, "run", fake_run)

    events = romcal_adapter.fetch_calendar(2025, script_path=script)
    assert events == [{"date": "2025-01-01", "name": "Mary"}]


def test_fetch_calendar_raises_on_failure(monkeypatch, tmp_path):
    script = tmp_path / "romcal_fetch.mjs"
    script.write_text("console.log('stub');\n")

    def fake_run(command, capture_output, text, check):
        return DummyProcess(stderr='romcal error', returncode=1)

    monkeypatch.setattr(romcal_adapter.subprocess, "run", fake_run)

    with pytest.raises(romcal_adapter.RomcalRuntimeError):
        romcal_adapter.fetch_calendar(2025, script_path=script)
