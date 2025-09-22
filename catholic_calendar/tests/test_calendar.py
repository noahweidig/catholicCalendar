"""Tests for converting romcal data into ICS feeds."""

from __future__ import annotations

import datetime as dt

import pytest

from catholic_calendar.calendar import CalendarConfig, build_icalendar


@pytest.fixture
def sample_events() -> list[dict[str, object]]:
    """Return a handful of romcal-like events for tests."""

    return [
        {
            "date": "2025-01-01",
            "name": "Mary, Mother of God",
            "rankName": "SOLEMNITY",
            "liturgicalColor": "white",
            "isHolyDayOfObligation": True,
            "season": "Christmastide",
            "type": "Proper of Time",
            "note": "Patronal feast in many countries.",
        },
        {
            "date": dt.date(2025, 2, 2),
            "name": "Presentation of the Lord",
            "rankName": "FEAST",
            "liturgicalColors": ["white"],
            "season": "Ordinary Time",
            "type": "Proper of Time",
            "metadata": {"source": "General Roman Calendar"},
        },
        {
            "date": "2025-04-20",
            "name": "Easter Sunday",
            "rankName": "SOLEMNITY",
            "liturgicalColor": "white",
            "season": "Easter",
            "type": "Triduum",
            "commemorations": ["Resurrection of the Lord"],
        },
    ]


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


def test_build_calendar_contains_expected_events(sample_events):
    ics = build_icalendar(sample_events, CalendarConfig(name="Test Calendar"))

    assert ics.startswith("BEGIN:VCALENDAR")
    events = _extract_events(ics)
    assert len(events) == len(sample_events)

    summaries = {line.split(":", 1)[1] for event in events for line in event if line.startswith("SUMMARY:")}
    assert "Mary\\, Mother of God" in summaries
    assert "Easter Sunday" in summaries

    easter_event = next(event for event in events if any(line.endswith("Easter Sunday") for line in event))
    dtstart_line = next(line for line in easter_event if line.startswith("DTSTART"))
    assert dtstart_line.endswith("20250420")
    description_line = next(line for line in easter_event if line.startswith("DESCRIPTION:"))
    assert "Commemorations" in description_line
    assert "Season" in description_line


def test_build_calendar_sorts_events(sample_events):
    unordered = list(reversed(sample_events))
    ics = build_icalendar(unordered, CalendarConfig(name="Sorted"))
    events = _extract_events(ics)
    dates = [
        next(line.split(":", 1)[1] for line in event if line.startswith("DTSTART"))
        for event in events
    ]
    assert dates == sorted(dates)
