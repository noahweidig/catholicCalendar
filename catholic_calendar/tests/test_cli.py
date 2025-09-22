"""Tests for the command line interface."""

from __future__ import annotations

from pathlib import Path

import pytest

from catholic_calendar import cli


def _extract_events(ics: str) -> list[list[str]]:
    events = []
    lines = ics.replace("\r", "").split("\n")
    current: list[str] | None = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            current = []
        elif line == "END:VEVENT" and current is not None:
            events.append(current)
            current = None
        elif line.startswith(" ") and current is not None:
            current[-1] += line[1:]
        elif current is not None:
            current.append(line)
    return events


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    return tmp_path / "calendar.ics"


def test_main_creates_calendar(tmp_output: Path, monkeypatch):
    calls: list[tuple[int, dict[str, object]]] = []

    def fake_fetch(year: int, **kwargs):
        calls.append((year, kwargs))
        return [
            {
                "date": f"{year}-01-01",
                "name": f"Mary {year}",
                "rankName": "SOLEMNITY",
                "liturgicalColor": "white",
            }
        ]

    monkeypatch.setattr(cli, "fetch_calendar", fake_fetch)

    cli.main([
        "2025",
        "2026",
        "--output",
        str(tmp_output),
        "--name",
        "My Calendar",
        "--domain",
        "example.com",
    ])

    assert tmp_output.exists()
    ics = tmp_output.read_text(encoding="utf-8")
    events = _extract_events(ics)
    summaries = {line.split(":", 1)[1] for event in events for line in event if line.startswith("SUMMARY:")}
    assert "Mary 2025" in summaries
    assert "Mary 2026" in summaries

    assert calls[0][0] == 2025
    assert calls[0][1]["locale"] == "en"
    assert calls[0][1]["include_optional"] is True


def test_parse_args_allows_customisation():
    args = cli.parse_args(
        [
            "2025",
            "--output",
            "out.ics",
            "--locale",
            "es",
            "--calendar",
            "unitedStates",
            "--prodid=-//Custom//Prod//EN",
            "--timezone",
            "America/Chicago",
            "--exclude-optional",
        ]
    )

    assert args.locale == "es"
    assert args.calendar == "unitedStates"
    assert args.include_optional is False
    assert args.timezone == "America/Chicago"
