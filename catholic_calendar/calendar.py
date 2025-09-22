"""Utilities to build an iCalendar feed from romcal data."""

from __future__ import annotations

import datetime as dt
import json
import re
import uuid
from dataclasses import dataclass
from typing import Any, Iterable, List, Mapping, MutableMapping, Sequence


@dataclass
class CalendarConfig:
    """Options that control how the final iCalendar feed is produced."""

    name: str = "General Roman Calendar"
    prodid: str = "-//Catholic Calendar//General Roman Calendar//EN"
    domain: str = "catholic.calendar"
    timezone: str = "UTC"


_SLUG_RE = re.compile(r"[^a-z0-9]+")
_MAX_LINE_LENGTH = 75


def _slugify(value: str) -> str:
    """Create a filesystem and UID friendly slug from an arbitrary string."""

    if not value:
        return "event"
    value = value.lower()
    value = _SLUG_RE.sub("-", value)
    value = value.strip("-")
    return value or "event"


def _escape_text(value: str) -> str:
    """Escape characters according to RFC 5545."""

    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _fold_line(line: str) -> List[str]:
    """Fold long ICS lines to respect the 75 character limit."""

    if len(line) <= _MAX_LINE_LENGTH:
        return [line]
    chunks = [line[:_MAX_LINE_LENGTH]]
    remainder = line[_MAX_LINE_LENGTH:]
    while len(remainder) > _MAX_LINE_LENGTH - 1:
        chunks.append(" " + remainder[: _MAX_LINE_LENGTH - 1])
        remainder = remainder[_MAX_LINE_LENGTH - 1 :]
    chunks.append(" " + remainder)
    return chunks


def _format_ics_line(key: str, value: str) -> List[str]:
    return _fold_line(f"{key}:{value}")


def _parse_date(value: Any) -> dt.date:
    """Parse a date from romcal output into a :class:`datetime.date`."""

    if isinstance(value, dt.date):
        return value
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, (int, float)):
        return dt.datetime.utcfromtimestamp(value).date()
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value[:10])
        except ValueError:
            try:
                return dt.datetime.fromisoformat(value).date()
            except ValueError as exc:  # pragma: no cover - defensive branch
                raise ValueError(f"Cannot parse date from {value!r}") from exc
    raise TypeError(f"Unsupported date value {value!r}")


def _stringify(value: Any) -> str:
    """Convert a romcal value to a human readable string."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return ", ".join(_stringify(elem) for elem in value if elem is not None)
    if isinstance(value, Mapping):
        return "; ".join(
            f"{key}: {_stringify(val)}" for key, val in value.items() if val is not None
        )
    return json.dumps(value, ensure_ascii=False)


def _normalise_event(
    event: Mapping[str, Any], config: CalendarConfig
) -> MutableMapping[str, Any]:
    """Turn a romcal event dictionary into an iCalendar ready mapping."""

    if "date" in event:
        date_value = _parse_date(event["date"])
    elif "start" in event:
        date_value = _parse_date(event["start"])
    else:  # pragma: no cover - defensive branch
        raise KeyError("romcal events must include a 'date' entry")

    summary = (
        event.get("name")
        or event.get("title")
        or event.get("celebration")
        or event.get("id")
        or "Unnamed Celebration"
    )

    category = (
        event.get("rankName")
        or event.get("rank")
        or event.get("type")
        or event.get("classification")
        or "Celebration"
    )

    uid = event.get("uid") or event.get("identifier")
    if uid:
        uid = str(uid)
        if "@" not in uid:
            uid = f"{uid}@{config.domain}"
    else:
        slug = event.get("slug") or _slugify(summary)
        uid_seed = f"{date_value.isoformat()}-{slug}"
        uid = f"{uuid.uuid5(uuid.NAMESPACE_URL, uid_seed)}@{config.domain}"

    description_lines: List[str] = []
    description_pairs = [
        ("Rank", event.get("rankName") or event.get("rank")),
        ("Liturgical color", event.get("liturgicalColor") or event.get("liturgicalColors")),
        ("Season", event.get("season") or event.get("liturgicalSeason")),
        ("Type", event.get("type") or event.get("liturgicalType")),
        ("Holy day of obligation", event.get("isHolyDayOfObligation")),
        ("Optional memorial", event.get("isOptional")),
        ("Week", event.get("week") or event.get("liturgicalWeek")),
        ("Cycle", event.get("cycle") or event.get("liturgicalCycle")),
    ]
    notes = event.get("note") or event.get("notes")
    if notes:
        description_pairs.append(("Notes", notes))

    commemorations = event.get("commemorations") or event.get("secondaryCelebrations")
    if commemorations:
        description_lines.append("Commemorations: " + _stringify(commemorations))

    metadata = event.get("metadata") or event.get("meta")
    if metadata:
        description_lines.append(_stringify(metadata))

    for label, value in description_pairs:
        if value is None:
            continue
        stringified = _stringify(value)
        if stringified:
            description_lines.append(f"{label}: {stringified}")

    description = "\n".join(description_lines)

    categories = [category] if isinstance(category, str) else list(category)

    return {
        "uid": uid,
        "summary": summary,
        "description": description,
        "categories": categories,
        "date": date_value,
    }


def build_icalendar(
    events: Iterable[Mapping[str, Any]], config: CalendarConfig | None = None
) -> str:
    """Build a string containing the iCalendar representation of the events."""

    cfg = config or CalendarConfig()

    normalised_events = [_normalise_event(event, cfg) for event in events]
    normalised_events.sort(key=lambda item: (item["date"], item["summary"]))

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines: List[str] = [
        "BEGIN:VCALENDAR",
        f"PRODID:{cfg.prodid}",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_escape_text(cfg.name)}",
        f"X-WR-TIMEZONE:{_escape_text(cfg.timezone)}",
    ]

    for normalised in normalised_events:
        start = normalised["date"].strftime("%Y%m%d")
        end = (normalised["date"] + dt.timedelta(days=1)).strftime("%Y%m%d")
        lines.append("BEGIN:VEVENT")
        lines.extend(_format_ics_line("UID", normalised["uid"]))
        lines.extend(_format_ics_line("DTSTAMP", now))
        lines.extend(_format_ics_line("DTSTART;VALUE=DATE", start))
        lines.extend(_format_ics_line("DTEND;VALUE=DATE", end))
        lines.extend(_format_ics_line("SUMMARY", _escape_text(normalised["summary"])))
        if normalised["description"]:
            lines.extend(
                _format_ics_line("DESCRIPTION", _escape_text(normalised["description"]))
            )
        for category in normalised["categories"]:
            lines.extend(_format_ics_line("CATEGORIES", _escape_text(str(category))))
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
